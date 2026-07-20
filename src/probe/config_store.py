"""
Configuration storage with OS keychain for token.

Non-secret config lives in plain JSON at LEDGER_CONFIG_PATH (default
<data_dir>/config.json). The API token is stored via the OS native
secret store (Windows Credential Manager / macOS Keychain / Linux
Secret Service) using the `keyring` library — never written to disk
in plaintext, never logged, never exported.

Layout:
    config.json:
        vendor         = "zhipu" | "deepseek" | "openai" | "anthropic" | "relay"
        plan           = "zhipu-glm-pro" | "deepseek-paygo" | ... (user-selected)
        upstream_url   = e.g. https://open.bigmodel.cn/api/anthropic
        listen_port    = 8080
        monitor_url    = e.g. https://open.bigmodel.cn/api/monitor/usage/quota/limit
        monitor_interval_s = 300
        opt_in_upload  = true | false
        user_hash      = sha256(token + salt)[:16]   # token is NOT stored here
        salt           = random 16-byte hex (generated on first run)

Token is fetched on demand via get_token(); never persisted in config.json.
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

# ── Path resolution ────────────────────────────────────────────────────────

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_KEYRING_SERVICE = "llm-api-ledger"
_KEYRING_USER = "api-token"


def get_config_path() -> Path:
    env = os.environ.get("LEDGER_CONFIG")
    if env:
        return Path(env)
    data_dir = os.environ.get("LEDGER_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "config.json"
    return _DEFAULT_DATA_DIR / "config.json"


# ── Vendor registry ───────────────────────────────────────────────────────
# URL prefixes are exposed to the IDE: user changes base_url to
# http://127.0.0.1:8080/<prefix>/... and the probe routes accordingly.

VENDORS: dict[str, dict[str, Any]] = {
    "zhipu": {
        "label": "智谱 GLM Coding Plan (国内)",
        "url_prefix": "zhipu",
        "upstream_default": "https://open.bigmodel.cn/api/anthropic",
        "monitor_url_default": "https://open.bigmodel.cn/api/monitor/usage/quota/limit",
        "monitor_strips_suffix": "/anthropic",  # strip from upstream before monitor call
        "auth_header": "Authorization",  # raw token value (智谱 format)
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
        "monitor_strips_suffix": "/anthropic",
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
        "monitor_url_default": "",  # DeepSeek has no public monitor API yet
        "monitor_strips_suffix": "",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "plans": [
            {"id": "deepseek-paygo", "label": "DeepSeek 按量计费"},
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
        # User-defined 中转站: base_url + plan 自定义
        "label": "中转站 (自定义)",
        "url_prefix": "relay",
        "upstream_default": "",  # user fills
        "monitor_url_default": "",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
        "plans": [],  # user-defined
    },
}


def vendor_by_prefix(prefix: str) -> dict[str, Any] | None:
    for v in VENDORS.values():
        if v["url_prefix"] == prefix:
            return v
    return None


# ── Config load / save ────────────────────────────────────────────────────


def default_config() -> dict[str, Any]:
    return {
        "vendor": "zhipu",
        "plan": "zhipu-glm-pro",
        "upstream_url": VENDORS["zhipu"]["upstream_default"],
        "monitor_url": VENDORS["zhipu"]["monitor_url_default"],
        "listen_port": 8080,
        "monitor_interval_s": 300,
        "opt_in_upload": True,
        "salt": secrets.token_hex(16),
        "user_hash": "",  # filled by recompute_user_hash after token set
        "relay_plan_label": "",  # only used when vendor=relay
    }


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return default_config()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        merged = default_config()
        merged.update(data)
        return merged
    except Exception as e:
        logger.warning("load_config failed (%s), using defaults", e)
        return default_config()


def save_config(cfg: dict[str, Any]) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Defensive: strip any token-like fields before persisting
    safe = {k: v for k, v in cfg.items() if k.lower() not in {"token", "api_key", "apikey", "secret"}}
    with path.open("w", encoding="utf-8") as f:
        json.dump(safe, f, ensure_ascii=False, indent=2)


# ── Token: OS keychain, never plaintext ───────────────────────────────────


def _keyring_get(service: str, user: str) -> str | None:
    try:
        import keyring  # type: ignore

        return keyring.get_password(service, user) or None
    except Exception as e:
        logger.warning("keyring get failed (%s); falling back to env", e)
        # Fallback: read from env var only (still not written to disk by us)
        return os.environ.get("LEDGER_TOKEN")


def _keyring_set(service: str, user: str, value: str) -> bool:
    try:
        import keyring  # type: ignore

        keyring.set_password(service, user, value)
        return True
    except Exception as e:
        logger.warning("keyring set failed (%s); token not persisted", e)
        return False


def get_token() -> str | None:
    """Return the API token from keychain (or env fallback). Never logs it."""
    return _keyring_get(_KEYRING_SERVICE, _KEYRING_USER)


def set_token(value: str) -> bool:
    """Persist the API token to keychain. Returns True on success."""
    return _keyring_set(_KEYRING_SERVICE, _KEYRING_USER, value)


def has_token() -> bool:
    return bool(get_token())


# ── user_hash = sha256(token + salt)[:16] ──────────────────────────────────


def compute_user_hash(token: str, salt: str) -> str:
    if not token:
        return ""
    raw = f"{token}:{salt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def recompute_user_hash(cfg: dict[str, Any]) -> str:
    """Recompute user_hash from current token + salt and persist."""
    token = get_token() or ""
    h = compute_user_hash(token, cfg.get("salt", ""))
    cfg["user_hash"] = h
    save_config(cfg)
    return h


def token_last4() -> str:
    """Return last 4 chars of token, for PR-package provenance only."""
    t = get_token() or ""
    return t[-4:] if len(t) >= 4 else ""


def mask_token_for_log(token: str | None) -> str:
    """For logging: show only last4. Never log full token."""
    if not token:
        return "<empty>"
    if len(token) <= 4:
        return "***"
    return f"***{token[-4:]}"
