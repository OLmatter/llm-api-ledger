"""
Monitor-API poller (multi-key).

Loops over every active key in DB, calls its vendor's monitor endpoint,
parses the response, and writes one quota_snapshots row per period.

Per-vendor parsing:
  - zhipu / zaiglobal: /api/monitor/usage/quota/limit returns
    {"data": {"limits": [{"type": "TOKENS_LIMIT", "unit": 3|6, "percentage": 0..1}, ...]}}
  - minimax: /v1/api/openplatform/coding_plan/remains returns
    {"model_remains": [{"current_interval_remaining_percent": 0..1, ...}]}
    (note: MiniMax returns REMAINING %, we invert to USED %)
  - others (deepseek/openai/anthropic): no monitor API; poll is a no-op

Reference:
  - 智谱: github.com/zai-org/zai-coding-plugins (query-usage.mjs)
  - 智谱 weekly: github.com/jukanntenn/glm-plan-usage (src/api/client.rs)
  - MiniMax: github.com/JochenYang/minimax-status (cli/api.js)
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

TOKENS_LIMIT = "TOKENS_LIMIT"
TIME_LIMIT = "TIME_LIMIT"
PERIOD_5H = 3
PERIOD_WEEKLY = 6


# ── Per-vendor response parsers ───────────────────────────────────────────


def _classify_period(limit_obj: dict[str, Any]) -> tuple[str, int]:
    """Map 智谱 limit object to (period_type, period_unit)."""
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


def _extract_zhipu_periods(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse 智谱 / Z.ai /quota/limit payload (limits array)."""
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
        # 智谱 returns percentage as 0-100 integer (e.g. 30 = 30%)
        pct = float(lim.get("percentage") or 0)
        if pct > 1.0:
            pct = pct / 100.0
        out.append({
            "period_type": ptype,
            "period_unit": punit,
            "percentage": pct,
            "current_value": float(lim.get("currentValue") or lim.get("current_value") or 0),
            "limit_value": float(lim.get("limit") or lim.get("usage") or lim.get("limit_value") or lim.get("number") or 0),
            "raw": lim,
        })
    return out


def _extract_minimax_periods(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse MiniMax /coding_plan/remains payload.

    NOTE: MiniMax returns REMAINING percent. We invert to USED percent so
    the dashboard rendering is uniform across vendors.
    """
    out: list[dict[str, Any]] = []
    models = payload.get("model_remains") or []
    if not isinstance(models, list) or not models:
        return out
    m = models[0]
    if not isinstance(m, dict):
        return out

    def _used(remaining_pct: Any) -> float:
        if remaining_pct is None:
            return 0.0
        pct = float(remaining_pct)
        # MiniMax returns 0-100 integer, normalize to 0-1
        if pct > 1.0:
            pct = pct / 100.0
        return max(0.0, 1.0 - pct)

    # 5h rolling window
    total_5h = float(m.get("current_interval_total_count") or 0)
    rem_pct_5h = m.get("current_interval_remaining_percent")
    if total_5h > 0 or rem_pct_5h is not None:
        used_5h = _used(rem_pct_5h)
        out.append({
            "period_type": "tokens_5h",
            "period_unit": 3,
            "percentage": used_5h,
            "current_value": round(total_5h * used_5h) if total_5h > 0 else 0,
            "limit_value": total_5h,
            "raw": {"model": m.get("model_name", ""), "remaining_percent": rem_pct_5h, "total": total_5h},
        })
    # Weekly
    total_w = float(m.get("current_weekly_total_count") or 0)
    rem_pct_w = m.get("current_weekly_remaining_percent")
    if total_w > 0 or rem_pct_w is not None:
        used_w = _used(rem_pct_w)
        out.append({
            "period_type": "tokens_weekly",
            "period_unit": 6,
            "percentage": used_w,
            "current_value": round(total_w * used_w) if total_w > 0 else 0,
            "limit_value": total_w,
            "raw": {"model": m.get("model_name", ""), "remaining_percent": rem_pct_w, "total": total_w},
        })
    return out


_PARSERS = {
    "zhipu": _extract_zhipu_periods,
    "zaiglobal": _extract_zhipu_periods,
    "minimax": _extract_minimax_periods,
}


def _parse_for_vendor(vendor: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    parser = _PARSERS.get(vendor)
    if not parser:
        return []
    return parser(payload)


# ── Per-key polling ───────────────────────────────────────────────────────


async def poll_key(db_path, key_row: dict[str, Any], salt: str) -> list[dict[str, Any]]:
    """Poll monitor API for one key. Returns parsed periods (empty if no
    monitor URL, no token, or request failed)."""
    monitor_url = key_row.get("monitor_url") or ""
    if not monitor_url:
        return []
    label = key_row["label"]
    token = config_store.get_token_for_key(label) or ""
    if not token:
        logger.warning("monitor: key %r has no token in keychain, skipping", label)
        return []

    vendor = key_row.get("vendor", "")
    vinfo = config_store.VENDORS.get(vendor, {})
    auth_value = f"Bearer {token}" if vinfo.get("auth_scheme") == "Bearer" else token
    auth_header_name = vinfo.get("auth_header", "Authorization")

    headers = {
        auth_header_name: auth_value,
        "Accept-Language": "en-US,en",
        "Content-Type": "application/json",
    }
    if vinfo.get("monitor_referer"):
        headers["Referer"] = vinfo["monitor_referer"]

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(monitor_url, headers=headers)
        if resp.status_code != 200:
            logger.warning("monitor: key %r %s returned %d: %s",
                           label, monitor_url, resp.status_code, resp.text[:200])
            return []
        try:
            payload = resp.json()
        except Exception:
            logger.warning("monitor: key %r non-JSON response", label)
            return []
    except Exception as e:
        logger.warning("monitor: key %r poll failed: %s", label, e)
        return []

    periods = _parse_for_vendor(vendor, payload)
    ts = time.time()
    ts_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_hash = config_store.compute_user_hash(token, salt) if salt else ""
    for p in periods:
        snap = {
            "ts": ts,
            "ts_text": ts_text,
            "key_id": key_row["id"],
            "vendor": vendor,
            "plan": key_row.get("plan", ""),
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
        "monitor: polled %s/%s, %d periods",
        vendor, label, len(periods),
    )
    return periods


async def poll_once(db_path, salt: str) -> dict[str, list]:
    """Poll all active keys once. Returns {label: periods}."""
    keys = db.list_keys(db_path)
    active = [k for k in keys if k.get("is_active")]
    if not active:
        return {}
    results: dict[str, list] = {}
    # Poll concurrently to avoid serial latency when many keys
    tasks = [poll_key(db_path, k, salt) for k in active]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    for k, res in zip(active, gathered):
        if isinstance(res, Exception):
            logger.warning("monitor: key %r raised %s", k["label"], res)
            results[k["label"]] = []
        else:
            results[k["label"]] = res
    return results


async def poll_loop(db_path_getter, stop_event: asyncio.Event) -> None:
    """Background poll loop.

    db_path_getter: callable returning the current db Path (so it can change).
    Picks the shortest per-key interval and uses that as the loop cadence.
    """
    logger.info("monitor: loop started")
    failed_streak = 0
    while not stop_event.is_set():
        try:
            db_path = db_path_getter()
            salt = config_store.get_salt()
            keys = db.list_keys(db_path)
            active = [k for k in keys if k.get("is_active")]
            if not active:
                # No keys configured; idle longer
                wait = 60
            else:
                await poll_once(db_path, salt)
                failed_streak = 0
                # Use min interval across keys
                wait = min((int(k.get("monitor_interval_s") or 300) for k in active), default=300)
                wait = max(60, wait)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=wait)
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
