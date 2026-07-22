"""
Multi-key configuration store.

Each user-configured "key" is a (label, vendor, plan, token) tuple stored
in SQLite (db.keys table, see db.py) for metadata + OS keychain for the
actual token (keyed by label so multiple tokens can coexist).

API:
    list_keys()              → all keys from DB
    get_key(key_id)          → one key dict
    get_key_by_label(label)  → one key dict by label
    add_key(label, vendor, plan, upstream_url, monitor_url, token, ...)
                               → inserts DB row + stores token in keychain
    update_key(key_id, ...)  → patches DB row; if token given, updates keychain
    remove_key(key_id)       → deletes DB row + removes token from keychain
    get_token_for_key(label) → reads token from keychain (or None)
    compute_user_hash(token, salt)[:16]

The old single-config approach (load_config/save_config/get_token/set_token)
is kept for backward-compatibility during migration but is being phased out.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Any

logger = logging.getLogger("ledger.config")

# ── Paths ─────────────────────────────────────────────────────────────────

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_KEYRING_SERVICE = "llm-api-ledger"


def get_config_path() -> Path:
    """Path for the global (non-key) settings file: salt, listen_port, etc."""
    env = os.environ.get("LEDGER_CONFIG")
    if env:
        return Path(env)
    data_dir = os.environ.get("LEDGER_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "config.json"
    return _DEFAULT_DATA_DIR / "config.json"


# ── Vendor registry ───────────────────────────────────────────────────────

VENDORS: dict[str, dict[str, Any]] = {
    "volcengine": {
        "label": "火山方舟 Coding Plan",
        "url_prefix": "volcengine",
        # Coding Plan 走 /api/coding 路径（Anthropic 兼容层），不是通用 /api/v3
        # 数据源：GCMP 仓库 src/providers/config/volcengine.json
        "upstream_default": "https://ark.cn-beijing.volces.com/api/coding",
        "monitor_url_default": "",  # 火山无公开 monitor API
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "plans": [
            {"id": "volc-coding-lite", "label": "Coding Plan Lite (¥40/月)"},
            {"id": "volc-coding-pro", "label": "Coding Plan Pro (¥200/月)"},
        ],
    },
    "zhipu": {
        "label": "智谱 GLM Coding Plan (国内)",
        "url_prefix": "zhipu",
        "upstream_default": "https://open.bigmodel.cn/api/anthropic",
        "monitor_url_default": "https://open.bigmodel.cn/api/monitor/usage/quota/limit",
        "auth_header": "Authorization",
        "plans": [
            {"id": "zhipu-glm-lite", "label": "GLM Coding Plan Lite"},
            {"id": "zhipu-glm-pro", "label": "GLM Coding Plan Pro"},
            {"id": "zhipu-glm-max", "label": "GLM Coding Plan Max"},
        ],
    },
    "zaiglobal": {
        "label": "Z.ai GLM Coding Plan (国际)",
        "url_prefix": "zai",
        "upstream_default": "https://api.z.ai/api/anthropic",
        "monitor_url_default": "https://api.z.ai/api/monitor/usage/quota/limit",
        "auth_header": "Authorization",
        "plans": [
            {"id": "zai-glm-lite", "label": "Z.ai Lite"},
            {"id": "zai-glm-pro", "label": "Z.ai Pro"},
            {"id": "zai-glm-max", "label": "Z.ai Max"},
        ],
    },
    "deepseek": {
        "label": "DeepSeek (按量)",
        "url_prefix": "deepseek",
        "upstream_default": "https://api.deepseek.com",
        "monitor_url_default": "",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "plans": [
            {"id": "deepseek-paygo", "label": "DeepSeek 按量计费"},
        ],
    },
    "minimax": {
        "label": "MiniMax Token Plan (Coding Plan)",
        "url_prefix": "minimax",
        "upstream_default": "https://api.minimaxi.com/anthropic",
        "monitor_url_default": "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "monitor_referer": "https://platform.minimaxi.com/",
        "plans": [
            {"id": "minimax-tp-starter", "label": "Token Plan Starter (¥29/月)"},
            {"id": "minimax-tp-plus", "label": "Token Plan Plus (¥99/月)"},
            {"id": "minimax-tp-pro", "label": "Token Plan Pro (¥299/月)"},
            {"id": "minimax-tp-paygo", "label": "按量计费 (sk-xxxx)"},
        ],
    },
    "openai": {
        "label": "OpenAI",
        "url_prefix": "openai",
        "upstream_default": "https://api.openai.com/v1",
        "monitor_url_default": "",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "plans": [
            {"id": "openai-paygo", "label": "OpenAI 按量计费"},
        ],
    },
    "anthropic": {
        "label": "Anthropic",
        "url_prefix": "anthropic",
        "upstream_default": "https://api.anthropic.com/v1",
        "monitor_url_default": "",
        "auth_header": "x-api-key",
        "plans": [
            {"id": "anthropic-paygo", "label": "Anthropic 按量计费"},
        ],
    },
    "relay": {
        "label": "中转站 (自定义)",
        "url_prefix": "relay",
        "upstream_default": "",
        "monitor_url_default": "",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "plans": [],
    },
}


def vendor_by_prefix(prefix: str) -> dict[str, Any] | None:
    for v in VENDORS.values():
        if v["url_prefix"] == prefix:
            return v
    return None


def vendor_key_by_prefix(prefix: str) -> str | None:
    for k, v in VENDORS.items():
        if v["url_prefix"] == prefix:
            return k
    return None


# ── Global (non-key) config: salt, listen_port ────────────────────────────


def default_global_config() -> dict[str, Any]:
    return {
        "listen_port": 8080,
        "salt": secrets.token_hex(16),
    }


def load_global_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return default_global_config()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        merged = default_global_config()
        merged.update(data)
        return merged
    except Exception as e:
        logger.warning("load_global_config failed (%s), using defaults", e)
        return default_global_config()


def save_global_config(cfg: dict[str, Any]) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in cfg.items() if k.lower() not in {"token", "api_key", "apikey", "secret"}}
    with path.open("w", encoding="utf-8") as f:
        json.dump(safe, f, ensure_ascii=False, indent=2)


def get_salt() -> str:
    return load_global_config().get("salt", "")


# ── Keychain helpers ──────────────────────────────────────────────────────


def _keyring_get(service: str, user: str) -> str | None:
    try:
        import keyring  # type: ignore

        return keyring.get_password(service, user) or None
    except Exception as e:
        logger.warning("keyring get failed (%s); falling back to env", e)
        return os.environ.get("LEDGER_TOKEN")


def _keyring_set(service: str, user: str, value: str) -> bool:
    try:
        import keyring  # type: ignore

        keyring.set_password(service, user, value)
        return True
    except Exception as e:
        logger.warning("keyring set failed (%s); token not persisted", e)
        return False


def _keyring_delete(service: str, user: str) -> None:
    try:
        import keyring  # type: ignore

        keyring.delete_password(service, user)
    except Exception:
        pass


# ── Key CRUD (DB + keychain combined) ─────────────────────────────────────


def _token_keychain_id(label: str) -> str:
    """Stable id used as the keychain 'user' field, so multiple keys
    don't collide in the keychain."""
    return f"key:{label}"


def add_key(db_path, label: str, vendor: str, plan: str,
            upstream_url: str, monitor_url: str, token: str,
            monitor_interval_s: int = 300, notes: str = "",
            salt: str | None = None) -> dict[str, Any] | None:
    """Create a new key. Returns the new key dict, or None on failure
    (e.g. duplicate label)."""
    from . import db

    # Reject duplicate labels
    if db.get_key_by_label(db_path, label):
        logger.warning("add_key: label %r already exists", label)
        return None
    # Store token in keychain
    if token:
        ok = _keyring_set(_KEYRING_SERVICE, _token_keychain_id(label), token)
        if not ok:
            logger.warning("add_key: keychain store failed for %r", label)
    salt = salt or get_salt()
    user_hash = compute_user_hash(token, salt)
    token_last4 = token[-4:] if len(token) >= 4 else ""
    key_id = db.insert_key(db_path, {
        "label": label,
        "vendor": vendor,
        "plan": plan,
        "upstream_url": upstream_url,
        "monitor_url": monitor_url,
        "token_last4": token_last4,
        "keychain_id": _token_keychain_id(label),
        "monitor_interval_s": monitor_interval_s,
        "is_active": True,
        "created_at": __import__("time").time(),
        "notes": notes,
    })
    return db.get_key(db_path, key_id) if key_id else None


def update_key(db_path, key_id: int, updates: dict[str, Any],
               new_token: str | None = None, salt: str | None = None) -> dict[str, Any] | None:
    """Patch a key. If new_token is provided, updates keychain + recomputes
    user_hash + token_last4."""
    from . import db

    current = db.get_key(db_path, key_id)
    if not current:
        return None
    # If label is being renamed, we must move the keychain entry too
    new_label = updates.get("label")
    if new_token:
        target_label = new_label or current["label"]
        _keyring_set(_KEYRING_SERVICE, _token_keychain_id(target_label), new_token)
        s = salt or get_salt()
        updates = dict(updates)
        updates["token_last4"] = new_token[-4:] if len(new_token) >= 4 else ""
        updates["keychain_id"] = _token_keychain_id(target_label)
    if new_label and new_label != current["label"]:
        # Move keychain entry to new label
        old_token = _keyring_get(_KEYRING_SERVICE, _token_keychain_id(current["label"]))
        if old_token:
            _keyring_set(_KEYRING_SERVICE, _token_keychain_id(new_label), old_token)
            _keyring_delete(_KEYRING_SERVICE, _token_keychain_id(current["label"]))
        updates = dict(updates)
        updates["keychain_id"] = _token_keychain_id(new_label)
    db.update_key(db_path, key_id, updates)
    return db.get_key(db_path, key_id)


def remove_key(db_path, key_id: int) -> bool:
    """Delete a key from DB + keychain."""
    from . import db

    k = db.get_key(db_path, key_id)
    if not k:
        return False
    _keyring_delete(_KEYRING_SERVICE, _token_keychain_id(k["label"]))
    return db.delete_key(db_path, key_id)


def get_token_for_key(label: str) -> str | None:
    """Read token from keychain for a given key label."""
    return _keyring_get(_KEYRING_SERVICE, _token_keychain_id(label))


def list_keys(db_path):
    """List all keys (without tokens)."""
    from . import db

    return db.list_keys(db_path)


def get_key(db_path, key_id: int):
    from . import db

    return db.get_key(db_path, key_id)


def get_key_by_label(db_path, label: str):
    from . import db

    return db.get_key_by_label(db_path, label)


# ── Hashes ────────────────────────────────────────────────────────────────


def compute_user_hash(token: str, salt: str) -> str:
    if not token:
        return ""
    raw = f"{token}:{salt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def token_last4(token: str | None) -> str:
    if not token:
        return ""
    return token[-4:] if len(token) >= 4 else ""


def mask_token_for_log(token: str | None) -> str:
    if not token:
        return "<empty>"
    if len(token) <= 4:
        return "***"
    return f"***{token[-4:]}"


# ── Legacy single-token API (for migration / fallback) ────────────────────


def get_token() -> str | None:
    """Legacy: read the first available key's token. Used during migration
    before all code paths are key-aware."""
    # Try the original single-token keychain slot first
    t = _keyring_get(_KEYRING_SERVICE, "api-token")
    return t


def set_token(value: str) -> bool:
    """Legacy: store token in the original single-token slot."""
    return _keyring_set(_KEYRING_SERVICE, "api-token", value)


def has_token() -> bool:
    return bool(get_token())


def load_config() -> dict[str, Any]:
    """Legacy: return a config dict synthesised from global config.
    Modern code should use list_keys() / get_key() instead."""
    return load_global_config()


def save_config(cfg: dict[str, Any]) -> None:
    save_global_config(cfg)


def recompute_user_hash(cfg: dict[str, Any]) -> str:
    """Legacy no-op kept for backward compat. user_hash is now per-key."""
    return ""
