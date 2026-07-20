"""
SQLite storage for the probe.

Three tables:
- keys: user-configured API keys (label, vendor, plan, keychain ref)
- requests: one row per upstream API call (transparent proxy observation)
- quota_snapshots: one row per monitor-API poll (vendor-claimed usage)

All data is filtered by key_id at write and read time, so the dashboard
can show one key, several keys, or all keys aggregated.

Schema is migrated in-place via column-add; no destructive migrations.
All fields use INTEGER/TEXT so the DB is portable across OS.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("ledger.db")

# Default DB path: sibling of this file so PyInstaller bundle works.
# Override via LEDGER_DB env when running from source / tests.
_DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "ledger.db"


def get_db_path(override: str | None = None) -> Path:
    import os

    if override:
        return Path(override)
    env = os.environ.get("LEDGER_DB")
    if env:
        return Path(env)
    return _DEFAULT_DB


# ── Schema ────────────────────────────────────────────────────────────────

_KEYS_SCHEMA = """
CREATE TABLE IF NOT EXISTS keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    vendor TEXT NOT NULL DEFAULT '',
    plan TEXT NOT NULL DEFAULT '',
    upstream_url TEXT NOT NULL DEFAULT '',
    monitor_url TEXT NOT NULL DEFAULT '',
    token_last4 TEXT NOT NULL DEFAULT '',
    keychain_id TEXT NOT NULL DEFAULT '',
    monitor_interval_s INTEGER NOT NULL DEFAULT 300,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL,
    last_used_at REAL NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT ''
)
"""

_REQUESTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    ts_text TEXT NOT NULL,
    key_id INTEGER NOT NULL DEFAULT 0,
    vendor TEXT NOT NULL DEFAULT '',
    plan TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    endpoint TEXT NOT NULL DEFAULT '',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    ttft_ms INTEGER NOT NULL DEFAULT 0,
    total_latency_ms INTEGER NOT NULL DEFAULT 0,
    tps_mean REAL NOT NULL DEFAULT 0,
    status_code INTEGER NOT NULL DEFAULT 0,
    error_type TEXT NOT NULL DEFAULT '',
    error_message_hash TEXT NOT NULL DEFAULT '',
    timeout_type TEXT NOT NULL DEFAULT '',
    stop_signal TEXT NOT NULL DEFAULT '',
    user_hash TEXT NOT NULL DEFAULT '',
    request_did_complete INTEGER NOT NULL DEFAULT 0,
    num_messages INTEGER NOT NULL DEFAULT 0,
    effort TEXT NOT NULL DEFAULT ''
)
"""

_QUOTA_SCHEMA = """
CREATE TABLE IF NOT EXISTS quota_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    ts_text TEXT NOT NULL,
    key_id INTEGER NOT NULL DEFAULT 0,
    vendor TEXT NOT NULL DEFAULT '',
    plan TEXT NOT NULL DEFAULT '',
    period_type TEXT NOT NULL,
    period_unit INTEGER NOT NULL DEFAULT 0,
    percentage REAL NOT NULL DEFAULT 0,
    current_value REAL NOT NULL DEFAULT 0,
    limit_value REAL NOT NULL DEFAULT 0,
    raw_json TEXT NOT NULL DEFAULT '',
    user_hash TEXT NOT NULL DEFAULT ''
)
"""

_REQUESTS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_req_ts ON requests(ts)",
    "CREATE INDEX IF NOT EXISTS idx_req_key ON requests(key_id)",
    "CREATE INDEX IF NOT EXISTS idx_req_vendor ON requests(vendor)",
    "CREATE INDEX IF NOT EXISTS idx_req_model ON requests(model)",
    "CREATE INDEX IF NOT EXISTS idx_req_status ON requests(status_code)",
]

_QUOTA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_quota_ts ON quota_snapshots(ts)",
    "CREATE INDEX IF NOT EXISTS idx_quota_key ON quota_snapshots(key_id)",
    "CREATE INDEX IF NOT EXISTS idx_quota_vendor ON quota_snapshots(vendor)",
]

_KEYS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_keys_label ON keys(label)",
    "CREATE INDEX IF NOT EXISTS idx_keys_active ON keys(is_active)",
]

# Columns added via ALTER TABLE for forward-compatible migration.
_REQUESTS_MIGRATIONS: list[tuple[str, str, str]] = [
    ("requests", "ttft_ms", "INTEGER NOT NULL DEFAULT 0"),
    ("requests", "tps_mean", "REAL NOT NULL DEFAULT 0"),
    ("requests", "error_type", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "error_message_hash", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "timeout_type", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "stop_signal", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "user_hash", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "request_did_complete", "INTEGER NOT NULL DEFAULT 0"),
    ("requests", "vendor", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "plan", "TEXT NOT NULL DEFAULT ''"),
    ("requests", "key_id", "INTEGER NOT NULL DEFAULT 0"),
]

_QUOTA_MIGRATIONS: list[tuple[str, str, str]] = [
    ("quota_snapshots", "key_id", "INTEGER NOT NULL DEFAULT 0"),
]


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create tables, indexes, and apply additive migrations. Idempotent."""
    path = db_path or get_db_path()
    conn = _connect(path)
    try:
        conn.executescript(_KEYS_SCHEMA)
        conn.executescript(_REQUESTS_SCHEMA)
        conn.executescript(_QUOTA_SCHEMA)
        for stmt in _REQUESTS_INDEXES + _QUOTA_INDEXES + _KEYS_INDEXES:
            conn.execute(stmt)
        for table, col, decl in _REQUESTS_MIGRATIONS + _QUOTA_MIGRATIONS:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if col not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
                logger.info("migration: added %s.%s", table, col)
        conn.commit()
    finally:
        conn.close()


# ── Key CRUD ──────────────────────────────────────────────────────────────


def list_keys(db_path: Path) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT id, label, vendor, plan, upstream_url, monitor_url,
                      token_last4, keychain_id, monitor_interval_s,
                      is_active, created_at, last_used_at, notes
               FROM keys ORDER BY is_active DESC, id ASC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_key(db_path: Path, key_id: int) -> dict[str, Any] | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """SELECT id, label, vendor, plan, upstream_url, monitor_url,
                      token_last4, keychain_id, monitor_interval_s,
                      is_active, created_at, last_used_at, notes
               FROM keys WHERE id = ?""",
            (key_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_key_by_label(db_path: Path, label: str) -> dict[str, Any] | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """SELECT id, label, vendor, plan, upstream_url, monitor_url,
                      token_last4, keychain_id, monitor_interval_s,
                      is_active, created_at, last_used_at, notes
               FROM keys WHERE label = ?""",
            (label,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def insert_key(db_path: Path, k: dict[str, Any]) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO keys
               (label, vendor, plan, upstream_url, monitor_url,
                token_last4, keychain_id, monitor_interval_s,
                is_active, created_at, last_used_at, notes)
               VALUES (:label, :vendor, :plan, :upstream_url, :monitor_url,
                       :token_last4, :keychain_id, :monitor_interval_s,
                       :is_active, :created_at, 0, :notes)""",
            {
                "label": k["label"],
                "vendor": k.get("vendor", ""),
                "plan": k.get("plan", ""),
                "upstream_url": k.get("upstream_url", ""),
                "monitor_url": k.get("monitor_url", ""),
                "token_last4": k.get("token_last4", ""),
                "keychain_id": k.get("keychain_id", ""),
                "monitor_interval_s": int(k.get("monitor_interval_s", 300) or 300),
                "is_active": 1 if k.get("is_active", True) else 0,
                "created_at": k.get("created_at", time.time()),
                "notes": k.get("notes", ""),
            },
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def update_key(db_path: Path, key_id: int, updates: dict[str, Any]) -> bool:
    if not updates:
        return False
    allowed = {"label", "vendor", "plan", "upstream_url", "monitor_url",
               "token_last4", "keychain_id", "monitor_interval_s",
               "is_active", "notes", "last_used_at"}
    sets = []
    vals: list[Any] = []
    for k, v in updates.items():
        if k not in allowed:
            continue
        if k == "is_active":
            v = 1 if v else 0
        sets.append(f"{k} = ?")
        vals.append(v)
    if not sets:
        return False
    vals.append(key_id)
    conn = _connect(db_path)
    try:
        conn.execute(f"UPDATE keys SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()
        return True
    finally:
        conn.close()


def delete_key(db_path: Path, key_id: int) -> bool:
    conn = _connect(db_path)
    try:
        cur = conn.execute("DELETE FROM keys WHERE id = ?", (key_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def touch_key_last_used(db_path: Path, key_id: int) -> None:
    conn = _connect(db_path)
    try:
        conn.execute("UPDATE keys SET last_used_at = ? WHERE id = ?", (time.time(), key_id))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


# ── Request writers ───────────────────────────────────────────────────────


def save_request(db_path: Path, rec: dict[str, Any]) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO requests
               (ts, ts_text, key_id, vendor, plan, model, endpoint,
                input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                ttft_ms, total_latency_ms, tps_mean, status_code,
                error_type, error_message_hash, timeout_type, stop_signal,
                user_hash, request_did_complete, num_messages, effort)
               VALUES (:ts, :ts_text, :key_id, :vendor, :plan, :model, :endpoint,
                       :input_tokens, :output_tokens, :cache_creation_tokens, :cache_read_tokens,
                       :ttft_ms, :total_latency_ms, :tps_mean, :status_code,
                       :error_type, :error_message_hash, :timeout_type, :stop_signal,
                       :user_hash, :request_did_complete, :num_messages, :effort)""",
            {
                "ts": rec.get("ts", time.time()),
                "ts_text": rec.get("ts_text", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "key_id": int(rec.get("key_id", 0) or 0),
                "vendor": rec.get("vendor", ""),
                "plan": rec.get("plan", ""),
                "model": rec.get("model", ""),
                "endpoint": rec.get("endpoint", ""),
                "input_tokens": int(rec.get("input_tokens", 0) or 0),
                "output_tokens": int(rec.get("output_tokens", 0) or 0),
                "cache_creation_tokens": int(rec.get("cache_creation_tokens", 0) or 0),
                "cache_read_tokens": int(rec.get("cache_read_tokens", 0) or 0),
                "ttft_ms": int(rec.get("ttft_ms", 0) or 0),
                "total_latency_ms": int(rec.get("total_latency_ms", 0) or 0),
                "tps_mean": float(rec.get("tps_mean", 0) or 0),
                "status_code": int(rec.get("status_code", 0) or 0),
                "error_type": rec.get("error_type", "") or "",
                "error_message_hash": rec.get("error_message_hash", "") or "",
                "timeout_type": rec.get("timeout_type", "") or "",
                "stop_signal": rec.get("stop_signal", "") or "",
                "user_hash": rec.get("user_hash", "") or "",
                "request_did_complete": 1 if rec.get("request_did_complete") else 0,
                "num_messages": int(rec.get("num_messages", 0) or 0),
                "effort": rec.get("effort", "") or "",
            },
        )
        conn.commit()
        return cur.lastrowid or 0
    except Exception as e:
        logger.error("save_request failed: %s", e)
        return 0
    finally:
        conn.close()


def save_quota_snapshot(db_path: Path, snap: dict[str, Any]) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO quota_snapshots
               (ts, ts_text, key_id, vendor, plan, period_type, period_unit,
                percentage, current_value, limit_value, raw_json, user_hash)
               VALUES (:ts, :ts_text, :key_id, :vendor, :plan, :period_type, :period_unit,
                       :percentage, :current_value, :limit_value, :raw_json, :user_hash)""",
            {
                "ts": snap.get("ts", time.time()),
                "ts_text": snap.get("ts_text", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "key_id": int(snap.get("key_id", 0) or 0),
                "vendor": snap.get("vendor", ""),
                "plan": snap.get("plan", ""),
                "period_type": snap.get("period_type", ""),
                "period_unit": int(snap.get("period_unit", 0) or 0),
                "percentage": float(snap.get("percentage", 0) or 0),
                "current_value": float(snap.get("current_value", 0) or 0),
                "limit_value": float(snap.get("limit_value", 0) or 0),
                "raw_json": snap.get("raw_json", "") or "",
                "user_hash": snap.get("user_hash", "") or "",
            },
        )
        conn.commit()
        return cur.lastrowid or 0
    except Exception as e:
        logger.error("save_quota_snapshot failed: %s", e)
        return 0
    finally:
        conn.close()


# ── Readers (all accept key_id=0 for "aggregate across all keys") ─────────


def _key_filter(key_id: int, alias: str = "") -> str:
    """Return a SQL fragment 'AND key = ?' for the given key_id, or '' if 0.
    `alias` is the column prefix (e.g. 'r' for 'r.key_id')."""
    col = f"{alias}.key_id" if alias else "key_id"
    return f"AND {col} = ?" if key_id else ""


def aggregate_stats(db_path: Path, key_id: int = 0, days: int = 30) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        since = time.time() - days * 86400
        kf = _key_filter(key_id)
        # SQL fragment is "WHERE ts > ? [AND key_id = ?]" so params order is (since[, key_id])
        since_params = (since, key_id) if key_id else (since,)

        total_row = conn.execute(
            f"""SELECT COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so,
                      COALESCE(SUM(cache_creation_tokens),0) scc,
                      COALESCE(SUM(cache_read_tokens),0) scr,
                      COALESCE(AVG(total_latency_ms),0) alat,
                      COALESCE(AVG(ttft_ms),0) attft,
                      COALESCE(AVG(tps_mean),0) atps
               FROM requests WHERE ts > ? {kf}""",
            since_params,
        ).fetchone()

        today = datetime.now().strftime("%Y-%m-%d")
        today_params = (f"{today}%", key_id) if key_id else (f"{today}%",)
        today_row = conn.execute(
            f"""SELECT COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so,
                      COALESCE(SUM(cache_creation_tokens),0) scc,
                      COALESCE(SUM(cache_read_tokens),0) scr
               FROM requests WHERE ts_text LIKE ? {kf}""",
            today_params,
        ).fetchone()

        status_rows = conn.execute(
            f"""SELECT status_code, COUNT(*) cnt
               FROM requests WHERE ts > ? {kf}
               GROUP BY status_code ORDER BY cnt DESC""",
            since_params,
        ).fetchall()

        timeout_rows = conn.execute(
            f"""SELECT timeout_type, COUNT(*) cnt
               FROM requests WHERE ts > ? {kf} AND timeout_type != ''
               GROUP BY timeout_type""",
            since_params,
        ).fetchall()

        # Per-vendor breakdown only meaningful when aggregating across keys
        if key_id:
            vendor_rows = []
        else:
            vendor_rows = conn.execute(
                """SELECT vendor, COUNT(*) cnt,
                          COALESCE(SUM(input_tokens),0) si,
                          COALESCE(SUM(output_tokens),0) so
                   FROM requests WHERE ts > ? GROUP BY vendor ORDER BY cnt DESC""",
                (since,),
            ).fetchall()

        recent_where = "WHERE key_id = ?" if key_id else ""
        recent_params: tuple = (key_id,) if key_id else ()
        recent = conn.execute(
            f"""SELECT id, ts_text, key_id, vendor, model, endpoint,
                      input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                      ttft_ms, total_latency_ms, tps_mean, status_code, error_type,
                      timeout_type, stop_signal
               FROM requests {recent_where} ORDER BY id DESC LIMIT 50""",
            recent_params,
        ).fetchall()

        daily = conn.execute(
            f"""SELECT SUBSTR(ts_text,1,10) day, COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so,
                      COALESCE(SUM(cache_creation_tokens),0) scc,
                      COALESCE(SUM(cache_read_tokens),0) scr
               FROM requests WHERE ts > ? {kf}
               GROUP BY day ORDER BY day ASC""",
            (time.time() - 30 * 86400, key_id) if key_id else (time.time() - 30 * 86400,),
        ).fetchall()

        quota_subfilter = "WHERE key_id = ?" if key_id else ""
        quota_subparams: tuple = (key_id,) if key_id else ()
        quota = conn.execute(
            f"""SELECT key_id, vendor, plan, period_type, period_unit, percentage,
                      current_value, limit_value, ts_text
               FROM quota_snapshots
               WHERE id IN (SELECT MAX(id) FROM quota_snapshots {quota_subfilter}
                            GROUP BY period_type, period_unit)
               ORDER BY vendor, period_type""",
            quota_subparams,
        ).fetchall()

        return {
            "key_id": key_id,
            "window_days": days,
            "total": dict(total_row) if total_row else {},
            "today": dict(today_row) if today_row else {},
            "status_breakdown": [dict(r) for r in status_rows],
            "timeout_breakdown": [dict(r) for r in timeout_rows],
            "vendor_breakdown": [dict(r) for r in vendor_rows],
            "recent": [dict(r) for r in recent],
            "daily": [dict(r) for r in daily],
            "quota": [dict(r) for r in quota],
        }
    finally:
        conn.close()


def hourly_series(db_path: Path, hours: int = 24, key_id: int = 0) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        now = int(time.time())
        start = now - hours * 3600
        kf = _key_filter(key_id)
        params = (start, key_id) if key_id else (start,)
        rows = conn.execute(
            f"""SELECT
                (CAST(ts AS INTEGER) / 3600) * 3600 AS bucket,
                COUNT(*) AS cnt,
                SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) AS ok,
                SUM(CASE WHEN timeout_type != '' THEN 1 ELSE 0 END) AS tmo,
                AVG(CASE WHEN ttft_ms > 0 THEN ttft_ms END) AS attft,
                AVG(CASE WHEN tps_mean > 0 THEN tps_mean END) AS atps,
                AVG(total_latency_ms) AS alat,
                SUM(input_tokens) AS si,
                SUM(output_tokens) AS so,
                SUM(cache_read_tokens) AS scr
               FROM requests WHERE ts >= ? {kf}
               GROUP BY bucket ORDER BY bucket ASC""",
            params,
        ).fetchall()
        out: list[dict[str, Any]] = []
        by_bucket = {r["bucket"]: r for r in rows}
        for h in range(hours, 0, -1):
            b = ((now - h * 3600) // 3600) * 3600
            r = by_bucket.get(b)
            if r:
                cnt = r["cnt"] or 0
                ok = r["ok"] or 0
                tmo = r["tmo"] or 0
                out.append({
                    "ts": b,
                    "hour_label": datetime.fromtimestamp(b).strftime("%H:00"),
                    "count": cnt,
                    "success_rate": (ok / cnt) if cnt else 0,
                    "timeout_rate": (tmo / cnt) if cnt else 0,
                    "avg_ttft": round(r["attft"] or 0),
                    "avg_tps": round(r["atps"] or 0, 1),
                    "avg_latency": round(r["alat"] or 0),
                    "input_tokens": r["si"] or 0,
                    "output_tokens": r["so"] or 0,
                    "cache_read_tokens": r["scr"] or 0,
                })
            else:
                out.append({
                    "ts": b,
                    "hour_label": datetime.fromtimestamp(b).strftime("%H:00"),
                    "count": 0, "success_rate": 0, "timeout_rate": 0,
                    "avg_ttft": 0, "avg_tps": 0, "avg_latency": 0,
                    "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
                })
        return out
    finally:
        conn.close()


def daily_series(db_path: Path, days: int = 7, key_id: int = 0) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        since = time.time() - days * 86400
        kf = _key_filter(key_id)
        params = (since, key_id) if key_id else (since,)
        rows = conn.execute(
            f"""SELECT
                SUBSTR(ts_text,1,10) AS day,
                COUNT(*) AS cnt,
                SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) AS ok,
                SUM(CASE WHEN timeout_type != '' THEN 1 ELSE 0 END) AS tmo,
                AVG(CASE WHEN ttft_ms > 0 THEN ttft_ms END) AS attft,
                AVG(total_latency_ms) AS alat,
                SUM(input_tokens) AS si,
                SUM(output_tokens) AS so,
                SUM(cache_read_tokens) AS scr,
                SUM(cache_creation_tokens) AS scc
               FROM requests WHERE ts >= ? {kf}
               GROUP BY day ORDER BY day ASC""",
            params,
        ).fetchall()
        out = []
        for r in rows:
            cnt = r["cnt"] or 0
            cr = r["scr"] or 0
            cc = r["scc"] or 0
            si = r["si"] or 0
            cache_total = si + cr + cc
            cache_hit = (cr / cache_total) if cache_total else 0
            out.append({
                "day": r["day"],
                "count": cnt,
                "success_rate": ((r["ok"] or 0) / cnt) if cnt else 0,
                "timeout_rate": ((r["tmo"] or 0) / cnt) if cnt else 0,
                "avg_ttft": round(r["attft"] or 0),
                "avg_latency": round(r["alat"] or 0),
                "input_tokens": si,
                "output_tokens": r["so"] or 0,
                "cache_read_tokens": cr,
                "cache_hit_rate": round(cache_hit, 3),
            })
        return out
    finally:
        conn.close()


def fetch_window(db_path: Path, start_ts: float, end_ts: float, key_id: int = 0) -> dict[str, Any]:
    """Export all requests + quota in a time window for PR-package generation."""
    conn = _connect(db_path)
    try:
        kf = _key_filter(key_id)
        req_params = (start_ts, end_ts, key_id) if key_id else (start_ts, end_ts)
        reqs = conn.execute(
            f"""SELECT ts, ts_text, key_id, vendor, plan, model, endpoint,
                      input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                      ttft_ms, total_latency_ms, tps_mean, status_code,
                      error_type, timeout_type, stop_signal, request_did_complete,
                      num_messages, effort
               FROM requests WHERE ts BETWEEN ? AND ? {kf} ORDER BY ts ASC""",
            req_params,
        ).fetchall()
        quotas = conn.execute(
            f"""SELECT ts, key_id, vendor, plan, period_type, period_unit,
                      percentage, current_value, limit_value
               FROM quota_snapshots WHERE ts BETWEEN ? AND ? {kf} ORDER BY ts ASC""",
            req_params,
        ).fetchall()
        return {
            "requests": [dict(r) for r in reqs],
            "quota_snapshots": [dict(r) for r in quotas],
        }
    finally:
        conn.close()
