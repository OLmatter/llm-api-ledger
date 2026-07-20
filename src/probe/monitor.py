"""
Monitor-API poller.

Calls the vendor's official usage endpoint (e.g. 智谱
/api/monitor/usage/quota/limit) at a fixed interval, extracts the
three independent quota periods (5h / weekly / 30d MCP), and persists
each as a quota_snapshots row.

Only 智谱 / Z.ai have a known public monitor endpoint today. For other
vendors, the poller is a no-op (logs once at startup, skips silently).

Reference for 智谱's three periods:
  - TOKENS_LIMIT + unit=3  → 5h rolling window
  - TOKENS_LIMIT + unit=6  → weekly quota
  - TIME_LIMIT             → 30d MCP tool usage

Source: zai-org/zai-coding-plugins + jukanntenn/glm-plan-usage (Rust).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any

import httpx

from . import config_store
from . import db

logger = logging.getLogger("ledger.monitor")

# Quota type constants from the official plugin source.
TOKENS_LIMIT = "TOKENS_LIMIT"
TIME_LIMIT = "TIME_LIMIT"

# Period-unit constants (jukanntenn/glm-plan-usage decoding).
PERIOD_5H = 3
PERIOD_WEEKLY = 6


def _classify_period(limit_obj: dict[str, Any]) -> tuple[str, int]:
    """Map a raw limit object to (period_type, period_unit).

    period_type values: 'tokens_5h' | 'tokens_weekly' | 'mcp_30d' | 'unknown'
    """
    t = (limit_obj.get("type") or "").upper()
    unit = int(limit_obj.get("unit") or 0)
    if t == TOKENS_LIMIT:
        if unit == PERIOD_5H:
            return ("tokens_5h", unit)
        if unit == PERIOD_WEEKLY:
            return ("tokens_weekly", unit)
        return ("tokens_other", unit)
    if t == TIME_LIMIT:
        return ("mcp_30d", unit)
    return ("unknown", unit)


def _extract_periods(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse /quota/limit payload into a list of period snapshots.

    The official plugin's response shape (confirmed from query-usage.mjs):
        {
          "data": {
            "limits": [
              {"type": "TOKENS_LIMIT", "unit": 3, "percentage": 0.42, ...},
              {"type": "TOKENS_LIMIT", "unit": 6, "percentage": 0.71, ...},
              {"type": "TIME_LIMIT",   "unit": 0, "percentage": 0.13, ...}
            ]
          }
        }
    """
    data = payload.get("data") or payload
    if isinstance(data, dict):
        limits = data.get("limits") or []
    elif isinstance(data, list):
        limits = data
    else:
        limits = []
    out: list[dict[str, Any]] = []
    if not isinstance(limits, list):
        return out
    for lim in limits:
        if not isinstance(lim, dict):
            continue
        ptype, punit = _classify_period(lim)
        out.append(
            {
                "period_type": ptype,
                "period_unit": punit,
                "percentage": float(lim.get("percentage") or 0),
                "current_value": float(lim.get("currentValue") or lim.get("current_value") or 0),
                "limit_value": float(lim.get("limit") or lim.get("usage") or lim.get("limit_value") or 0),
                "raw": lim,
            }
        )
    return out


async def poll_once(cfg: dict[str, Any], db_path) -> list[dict[str, Any]]:
    """Fetch quota/limit once and persist. Returns the parsed period list
    (empty if vendor has no monitor endpoint or the call failed)."""
    monitor_url = cfg.get("monitor_url") or ""
    if not monitor_url:
        return []
    token = config_store.get_token() or ""
    if not token:
        logger.warning("monitor: no token configured, skipping poll")
        return []

    # 智谱 expects the raw token in Authorization (not Bearer-prefixed).
    vendor = cfg.get("vendor", "")
    auth_value = token
    vinfo = config_store.VENDORS.get(vendor, {})
    if vinfo.get("auth_scheme") == "Bearer":
        auth_value = f"Bearer {token}"
    auth_header_name = vinfo.get("auth_header", "Authorization")

    headers = {
        auth_header_name: auth_value,
        "Accept-Language": "en-US,en",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(monitor_url, headers=headers)
        if resp.status_code != 200:
            logger.warning("monitor: %s returned %d: %s", monitor_url, resp.status_code, resp.text[:200])
            return []
        try:
            payload = resp.json()
        except Exception:
            logger.warning("monitor: non-JSON response from %s", monitor_url)
            return []
    except Exception as e:
        logger.warning("monitor: poll failed: %s", e)
        return []

    periods = _extract_periods(payload)
    ts = time.time()
    ts_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_hash = cfg.get("user_hash", "")
    vendor_id = cfg.get("vendor", "")
    plan_id = cfg.get("plan", "")
    for p in periods:
        snap = {
            "ts": ts,
            "ts_text": ts_text,
            "vendor": vendor_id,
            "plan": plan_id,
            "period_type": p["period_type"],
            "period_unit": p["period_unit"],
            "percentage": p["percentage"],
            "current_value": p["current_value"],
            "limit_value": p["limit_value"],
            "raw_json": json.dumps(p["raw"], ensure_ascii=False)[:4000],
            "user_hash": user_hash,
        }
        db.save_quota_snapshot(db_path, snap)
    logger.info(
        "monitor: polled %s, %d periods (5h=%s weekly=%s mcp=%s)",
        vendor_id,
        len(periods),
        _pct(periods, "tokens_5h"),
        _pct(periods, "tokens_weekly"),
        _pct(periods, "mcp_30d"),
    )
    return periods


def _pct(periods: list[dict[str, Any]], ptype: str) -> str:
    for p in periods:
        if p["period_type"] == ptype:
            return f"{p['percentage']*100:.1f}%" if isinstance(p["percentage"], float) else str(p["percentage"])
    return "n/a"


async def poll_loop(cfg_getter, db_path, stop_event: asyncio.Event) -> None:
    """Background poll loop. cfg_getter is a callable returning the current
    config dict (so we pick up config changes without restart)."""
    logger.info("monitor: loop started")
    failed_streak = 0
    while not stop_event.is_set():
        try:
            cfg = cfg_getter()
            interval = int(cfg.get("monitor_interval_s") or 300)
            interval = max(60, interval)  # floor at 1min to avoid hammering
            if cfg.get("monitor_url"):
                await poll_once(cfg, db_path)
                failed_streak = 0
            # wait but wake early on stop
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
        except Exception as e:
            failed_streak += 1
            logger.error("monitor loop error (streak=%d): %s", failed_streak, e)
            if failed_streak >= 5:
                logger.error("monitor: 5 consecutive failures, pausing 15min")
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=900)
                except asyncio.TimeoutError:
                    pass
                failed_streak = 0
    logger.info("monitor: loop stopped")
