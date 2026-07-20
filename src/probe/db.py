"""
SQLite storage for the probe.

Two tables:
- requests: one row per upstream API call (transparent proxy observation)
- quota_snapshots: one row per monitor-API poll (vendor-claimed usage)

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
    if override:
        return Path(override)
    env = __import__("os").environ.get("LEDGER_DB")
    if env:
        return Path(env)
    return _DEFAULT_DB


# ── Schema ────────────────────────────────────────────────────────────────

_REQUESTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    ts_text TEXT NOT NULL,
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
    "CREATE INDEX IF NOT EXISTS idx_req_vendor ON requests(vendor)",
    "CREATE INDEX IF NOT EXISTS idx_req_model ON requests(model)",
    "CREATE INDEX IF NOT EXISTS idx_req_status ON requests(status_code)",
]

_QUOTA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_quota_ts ON quota_snapshots(ts)",
    "CREATE INDEX IF NOT EXISTS idx_quota_vendor ON quota_snapshots(vendor)",
]

# Columns added via ALTER TABLE for forward-compatible migration.
# Each tuple: (table, column, decl). Idempotent: skipped if column exists.
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
        conn.executescript(_REQUESTS_SCHEMA)
        conn.executescript(_QUOTA_SCHEMA)
        for stmt in _REQUESTS_INDEXES + _QUOTA_INDEXES:
            conn.execute(stmt)
        # Additive migrations: ALTER TABLE ADD COLUMN (skip if present)
        for table, col, decl in _REQUESTS_MIGRATIONS:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if col not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
                logger.info("migration: added %s.%s", table, col)
        conn.commit()
    finally:
        conn.close()


# ── Writers ───────────────────────────────────────────────────────────────


def save_request(db_path: Path, rec: dict[str, Any]) -> int:
    """Insert one request observation. Returns the new row id."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO requests
               (ts, ts_text, vendor, plan, model, endpoint,
                input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                ttft_ms, total_latency_ms, tps_mean, status_code,
                error_type, error_message_hash, timeout_type, stop_signal,
                user_hash, request_did_complete, num_messages, effort)
               VALUES (:ts, :ts_text, :vendor, :plan, :model, :endpoint,
                       :input_tokens, :output_tokens, :cache_creation_tokens, :cache_read_tokens,
                       :ttft_ms, :total_latency_ms, :tps_mean, :status_code,
                       :error_type, :error_message_hash, :timeout_type, :stop_signal,
                       :user_hash, :request_did_complete, :num_messages, :effort)""",
            {
                "ts": rec.get("ts", time.time()),
                "ts_text": rec.get("ts_text", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
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
    """Insert one monitor-API quota snapshot. Returns the new row id."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO quota_snapshots
               (ts, ts_text, vendor, plan, period_type, period_unit,
                percentage, current_value, limit_value, raw_json, user_hash)
               VALUES (:ts, :ts_text, :vendor, :plan, :period_type, :period_unit,
                       :percentage, :current_value, :limit_value, :raw_json, :user_hash)""",
            {
                "ts": snap.get("ts", time.time()),
                "ts_text": snap.get("ts_text", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
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


# ── Readers ───────────────────────────────────────────────────────────────


def aggregate_stats(db_path: Path, days: int = 30) -> dict[str, Any]:
    """Return aggregate stats for the dashboard homepage."""
    conn = _connect(db_path)
    try:
        since = time.time() - days * 86400
        total_row = conn.execute(
            """SELECT COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so,
                      COALESCE(SUM(cache_creation_tokens),0) scc,
                      COALESCE(SUM(cache_read_tokens),0) scr,
                      COALESCE(AVG(total_latency_ms),0) alat,
                      COALESCE(AVG(ttft_ms),0) attft,
                      COALESCE(AVG(tps_mean),0) atps
               FROM requests WHERE ts > ?""",
            (since,),
        ).fetchone()
        today = datetime.now().strftime("%Y-%m-%d")
        today_row = conn.execute(
            """SELECT COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so,
                      COALESCE(SUM(cache_creation_tokens),0) scc,
                      COALESCE(SUM(cache_read_tokens),0) scr
               FROM requests WHERE ts_text LIKE ?""",
            (f"{today}%",),
        ).fetchone()
        # Status-code distribution
        status_rows = conn.execute(
            """SELECT status_code, COUNT(*) cnt
               FROM requests WHERE ts > ? GROUP BY status_code ORDER BY cnt DESC""",
            (since,),
        ).fetchall()
        # Timeout distribution
        timeout_rows = conn.execute(
            """SELECT timeout_type, COUNT(*) cnt
               FROM requests WHERE ts > ? AND timeout_type != '' GROUP BY timeout_type""",
            (since,),
        ).fetchall()
        # Per-vendor
        vendor_rows = conn.execute(
            """SELECT vendor, COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so
               FROM requests WHERE ts > ? GROUP BY vendor ORDER BY cnt DESC""",
            (since,),
        ).fetchall()
        # Recent 50
        recent = conn.execute(
            """SELECT id, ts_text, vendor, model, endpoint,
                      input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                      ttft_ms, total_latency_ms, tps_mean, status_code, error_type,
                      timeout_type, stop_signal
               FROM requests ORDER BY id DESC LIMIT 50"""
        ).fetchall()
        # Daily series (last 30 days)
        daily = conn.execute(
            """SELECT SUBSTR(ts_text,1,10) day, COUNT(*) cnt,
                      COALESCE(SUM(input_tokens),0) si,
                      COALESCE(SUM(output_tokens),0) so,
                      COALESCE(SUM(cache_creation_tokens),0) scc,
                      COALESCE(SUM(cache_read_tokens),0) scr
               FROM requests WHERE ts > ? GROUP BY day ORDER BY day ASC""",
            (time.time() - 30 * 86400,),
        ).fetchall()
        # Latest quota snapshots per vendor/period
        quota = conn.execute(
            """SELECT vendor, plan, period_type, period_unit, percentage,
                      current_value, limit_value, ts_text
               FROM quota_snapshots
               WHERE id IN (SELECT MAX(id) FROM quota_snapshots GROUP BY vendor, period_type, period_unit)
               ORDER BY vendor, period_type"""
        ).fetchall()
        return {
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


def fetch_window(db_path: Path, start_ts: float, end_ts: float) -> dict[str, Any]:
    """Export all requests + quota in a time window for PR-package generation."""
    conn = _connect(db_path)
    try:
        reqs = conn.execute(
            """SELECT ts, ts_text, vendor, plan, model, endpoint,
                      input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                      ttft_ms, total_latency_ms, tps_mean, status_code,
                      error_type, timeout_type, stop_signal, request_did_complete,
                      num_messages, effort
               FROM requests WHERE ts BETWEEN ? AND ? ORDER BY ts ASC""",
            (start_ts, end_ts),
        ).fetchall()
        quotas = conn.execute(
            """SELECT ts, vendor, plan, period_type, period_unit,
                      percentage, current_value, limit_value
               FROM quota_snapshots WHERE ts BETWEEN ? AND ? ORDER BY ts ASC""",
            (start_ts, end_ts),
        ).fetchall()
        return {
            "requests": [dict(r) for r in reqs],
            "quota_snapshots": [dict(r) for r in quotas],
        }
    finally:
        conn.close()
