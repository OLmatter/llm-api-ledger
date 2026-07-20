"""
PR-package export.

Generates a de-identified JSON bundle of the local probe data for a
given time window, suitable for contributing via GitHub PR (see
elm_1190120aa328 — the PR channel is the high-trust tier).

Privacy contract (hard rules, see project rule §10):
  - NEVER include: prompt content, code context, API key, user IP,
    full token
  - INCLUDE only: aggregate metrics (distributions, counts, rates) +
    raw event metadata (timestamps, model name, status code, latency
    band) + token last 4 chars (provenance only)
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from datetime import datetime, timedelta
from typing import Any

from . import config_store
from . import db


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((len(s) - 1) * p))
    return s[k]


def _aggregate_requests(reqs: list[dict[str, Any]]) -> dict[str, Any]:
    """Turn a list of request rows into aggregate distributions."""
    if not reqs:
        return {"count": 0}
    ttfts = [r["ttft_ms"] for r in reqs if r.get("ttft_ms")]
    tps_vals = [r["tps_mean"] for r in reqs if r.get("tps_mean")]
    latencies = [r["total_latency_ms"] for r in reqs if r.get("total_latency_ms")]
    statuses: dict[str, int] = {}
    for r in reqs:
        key = str(r.get("status_code") or 0)
        statuses[key] = statuses.get(key, 0) + 1
    timeouts: dict[str, int] = {}
    for r in reqs:
        t = r.get("timeout_type") or ""
        if t:
            timeouts[t] = timeouts.get(t, 0) + 1
    stop_signals: dict[str, int] = {}
    for r in reqs:
        s = r.get("stop_signal") or ""
        if s:
            stop_signals[s] = stop_signals.get(s, 0) + 1
    error_types: dict[str, int] = {}
    for r in reqs:
        e = r.get("error_type") or ""
        if e:
            error_types[e] = error_types.get(e, 0) + 1
    total_in = sum(r.get("input_tokens", 0) for r in reqs)
    total_out = sum(r.get("output_tokens", 0) for r in reqs)
    total_cc = sum(r.get("cache_creation_tokens", 0) for r in reqs)
    total_cr = sum(r.get("cache_read_tokens", 0) for r in reqs)
    cache_hit_pct = (total_cr / (total_in + total_cr + total_cc) * 100) if (total_in + total_cr + total_cc) > 0 else 0.0
    n = len(reqs)
    successes = sum(1 for r in reqs if 200 <= (r.get("status_code") or 0) < 300)
    timeouts_total = sum(timeouts.values())
    return {
        "count": n,
        "success_count": successes,
        "success_rate": successes / n if n else 0.0,
        "timeout_count": timeouts_total,
        "timeout_rate": timeouts_total / n if n else 0.0,
        "status_breakdown": statuses,
        "timeout_breakdown": timeouts,
        "stop_signal_breakdown": stop_signals,
        "error_type_breakdown": error_types,
        "tokens": {
            "input_total": total_in,
            "output_total": total_out,
            "cache_creation_total": total_cc,
            "cache_read_total": total_cr,
            "cache_hit_pct": round(cache_hit_pct, 2),
        },
        "ttft_ms": {
            "p50": _percentile(ttfts, 0.50),
            "p90": _percentile(ttfts, 0.90),
            "p99": _percentile(ttfts, 0.99),
            "max": max(ttfts) if ttfts else 0,
        },
        "tps_mean": {
            "p10": _percentile(tps_vals, 0.10),
            "p50": _percentile(tps_vals, 0.50),
            "p90": _percentile(tps_vals, 0.90),
        },
        "total_latency_ms": {
            "p50": _percentile(latencies, 0.50),
            "p90": _percentile(latencies, 0.90),
            "p99": _percentile(latencies, 0.99),
            "max": max(latencies) if latencies else 0,
        },
    }


def _aggregate_quota(quotas: list[dict[str, Any]]) -> dict[str, Any]:
    """Group quota snapshots by period_type and compute the latest + series tail."""
    by_period: dict[str, list[dict[str, Any]]] = {}
    for q in quotas:
        ptype = q.get("period_type") or "unknown"
        by_period.setdefault(ptype, []).append(q)
    out: dict[str, Any] = {}
    for ptype, items in by_period.items():
        items.sort(key=lambda x: x.get("ts", 0))
        latest = items[-1] if items else {}
        # Down-sample to at most 30 points for PR-package compactness
        step = max(1, len(items) // 30)
        series = [
            {"ts": it.get("ts"), "percentage": it.get("percentage", 0)}
            for it in items[::step]
        ]
        out[ptype] = {
            "samples": len(items),
            "latest_percentage": latest.get("percentage", 0),
            "latest_current_value": latest.get("current_value", 0),
            "latest_limit_value": latest.get("limit_value", 0),
            "series": series,
        }
    return out


def build_export_bundle(db_path, days: int = 7, key_id: int = 0) -> dict[str, Any]:
    """Build the full de-identified PR-package payload for the last `days` days.

    If key_id > 0, filters to that key's data only; otherwise aggregates
    across all keys.
    """
    end_ts = time.time()
    start_ts = end_ts - days * 86400
    window = db.fetch_window(db_path, start_ts, end_ts, key_id=key_id)
    reqs = window.get("requests", [])
    quotas = window.get("quota_snapshots", [])

    # If filtered to a key, derive vendor/plan/token_last4 from that key
    vendor = ""
    plan = ""
    token_last4 = ""
    user_hash = ""
    if key_id:
        k = db.get_key(db_path, key_id)
        if k:
            vendor = k.get("vendor", "")
            plan = k.get("plan", "")
            token_last4 = k.get("token_last4", "")
            salt = config_store.get_salt()
            tok = config_store.get_token_for_key(k["label"]) or ""
            user_hash = config_store.compute_user_hash(tok, salt)

    bundle = {
        "schema_version": 1,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "window": {
            "days": days,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "start_text": datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M:%S"),
            "end_text": datetime.fromtimestamp(end_ts).strftime("%Y-%m-%d %H:%M:%S"),
        },
        "key_id": key_id,
        "vendor": vendor,
        "plan": plan,
        "user_hash": user_hash,
        "token_last4": token_last4,
        "aggregates": {
            "requests": _aggregate_requests(reqs),
            "quota_by_period": _aggregate_quota(quotas),
        },
    }
    return bundle


def bundle_filename(bundle: dict[str, Any]) -> str:
    vendor = bundle.get("vendor", "unknown")
    plan = bundle.get("plan", "unknown")
    uh = bundle.get("user_hash", "nohash")[:8] or "nohash"
    end_ts = bundle.get("window", {}).get("end_ts")
    if end_ts:
        date = datetime.fromtimestamp(end_ts).strftime("%Y%m%d")
    else:
        date = datetime.now().strftime("%Y%m%d")
    return f"{vendor}_{plan}_{uh}_{date}.json"


def render_pr_description(bundle: dict[str, Any]) -> str:
    """Generate a Markdown body suitable for a GitHub PR description."""
    agg = bundle.get("aggregates", {}).get("requests", {})
    q = bundle.get("aggregates", {}).get("quota_by_period", {})
    lines = [
        "# 测试报告 PR",
        "",
        f"- **厂商**: `{bundle.get('vendor', '')}`",
        f"- **套餐**: `{bundle.get('plan', '')}`",
        f"- **时间窗**: {bundle.get('window', {}).get('start_text', '')} → {bundle.get('window', {}).get('end_text', '')}",
        f"- **数据点数**: {agg.get('count', 0)} 条请求",
        f"- **user_hash**: `{bundle.get('user_hash', '')}` (sha256(token+salt)[:16])",
        f"- **token_last4**: `***{bundle.get('token_last4', '')}`",
        "",
        "## 核心指标",
        "",
        f"- 成功率: {agg.get('success_rate', 0)*100:.1f}%",
        f"- 超时率: {agg.get('timeout_rate', 0)*100:.1f}%",
        f"- 缓存命中率: {agg.get('tokens', {}).get('cache_hit_pct', 0):.1f}%",
        f"- TTFT p50/p90/p99: {agg.get('ttft_ms', {}).get('p50', 0):.0f} / {agg.get('ttft_ms', {}).get('p90', 0):.0f} / {agg.get('ttft_ms', {}).get('p99', 0):.0f} ms",
        f"- TPS p50: {agg.get('tps_mean', {}).get('p50', 0):.1f} tok/s",
        "",
        "## 厂商声称额度（monitor API）",
        "",
    ]
    for ptype, info in q.items():
        lines.append(f"- **{ptype}**: {info.get('samples', 0)} samples, latest = {info.get('latest_percentage', 0)*100:.1f}% used")
    lines += [
        "",
        "## 状态码分布",
        "",
        "```json",
        json.dumps(agg.get("status_breakdown", {}), indent=2, ensure_ascii=False),
        "```",
        "",
        "## 超时类型分布",
        "",
        "```json",
        json.dumps(agg.get("timeout_breakdown", {}), indent=2, ensure_ascii=False),
        "```",
        "",
        "---",
        "",
        "本 PR 由 llm-api-ledger 探针自动生成。所有数据经过脱敏处理（无 prompt 内容、无 API key、无完整 token）。",
    ]
    return "\n".join(lines)
