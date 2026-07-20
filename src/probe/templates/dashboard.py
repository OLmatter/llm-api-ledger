"""
Dashboard HTML (server-side rendered, embedded in Python).

Route: /__ledger__/  and  /__ledger__

Shows:
  - Today + 30-day totals (tokens in/out, cache hit, latency, TTFT, TPS)
  - Status code distribution
  - Timeout-type distribution (4-way taxonomy)
  - Latest monitor quota per period (5h / weekly / 30d MCP)
  - Per-vendor breakdown
  - Daily series (last 30 days)
  - Recent 50 requests
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any


def _fmt_tokens(n: int | float | None) -> str:
    if not n:
        return "0"
    n = float(n)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{int(n)}"


def _fmt_latency(ms: float | None) -> str:
    if not ms:
        return "—"
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    return f"{ms:.0f}ms"


def _fmt_pct(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x*100:.1f}%"


def render(stats: dict[str, Any], cfg: dict[str, Any]) -> str:
    total = stats.get("total", {}) or {}
    today = stats.get("today", {}) or {}
    status_breakdown = stats.get("status_breakdown", []) or []
    timeout_breakdown = stats.get("timeout_breakdown", []) or []
    vendor_breakdown = stats.get("vendor_breakdown", []) or []
    recent = stats.get("recent", []) or []
    daily = stats.get("daily", []) or []
    quota = stats.get("quota", []) or []

    total_in = total.get("si", 0) or 0
    total_out = total.get("so", 0) or 0
    total_cc = total.get("scc", 0) or 0
    total_cr = total.get("scr", 0) or 0
    cache_total = total_in + total_cr + total_cc
    cache_hit = (total_cr / cache_total) if cache_total else 0
    today_in = today.get("si", 0) or 0
    today_out = today.get("so", 0) or 0

    vendor_label = cfg.get("vendor", "")
    plan_label = cfg.get("plan", "")
    has_token = cfg.get("has_token", False)

    # ── status code rows
    status_rows_html = ""
    if status_breakdown:
        max_n = max((r.get("cnt", 0) for r in status_breakdown), default=1) or 1
        for r in status_breakdown:
            sc = r.get("status_code", 0)
            cnt = r.get("cnt", 0)
            bar_w = int(cnt / max_n * 100)
            cls = "sc-2xx" if 200 <= sc < 300 else "sc-4xx" if 400 <= sc < 500 else "sc-5xx" if 500 <= sc < 600 else "sc-0"
            status_rows_html += (
                f"<tr><td class='{cls}'>{sc}</td><td>{cnt}</td>"
                f"<td><div class='bar {cls}' style='width:{bar_w}%'></div></td></tr>"
            )
    else:
        status_rows_html = "<tr><td colspan=3 class='muted'>暂无数据</td></tr>"

    # ── timeout rows
    timeout_rows_html = ""
    if timeout_breakdown:
        for r in timeout_breakdown:
            t = html.escape(str(r.get("timeout_type", "")))
            cnt = r.get("cnt", 0)
            timeout_rows_html += f"<tr><td><code>{t}</code></td><td>{cnt}</td></tr>"
    else:
        timeout_rows_html = "<tr><td colspan=2 class='muted'>无超时 ✓</td></tr>"

    # ── vendor rows
    vendor_rows_html = ""
    if vendor_breakdown:
        for r in vendor_breakdown:
            v = html.escape(str(r.get("vendor", "")) or "(unknown)")
            cnt = r.get("cnt", 0)
            si = _fmt_tokens(r.get("si", 0))
            so = _fmt_tokens(r.get("so", 0))
            vendor_rows_html += f"<tr><td>{v}</td><td>{cnt}</td><td>{si}</td><td>{so}</td></tr>"
    else:
        vendor_rows_html = "<tr><td colspan=4 class='muted'>暂无数据</td></tr>"

    # ── quota rows
    quota_html = ""
    if quota:
        for q in quota:
            ptype = html.escape(str(q.get("period_type", "")))
            pct = q.get("percentage", 0) or 0
            cur = _fmt_tokens(q.get("current_value", 0))
            lim = _fmt_tokens(q.get("limit_value", 0))
            bar_w = int(min(pct * 100, 100))
            bar_cls = "q-low" if pct < 0.7 else "q-mid" if pct < 0.9 else "q-high"
            ts = html.escape(str(q.get("ts_text", "")))
            quota_html += (
                f"<div class='quota-card'>"
                f"<div class='quota-head'><span class='ptype'>{ptype}</span>"
                f"<span class='muted small'>{ts}</span></div>"
                f"<div class='quota-bar-bg'><div class='quota-bar {bar_cls}' style='width:{bar_w}%'></div></div>"
                f"<div class='quota-foot'>{pct*100:.1f}% 已用"
                f" <span class='muted small'>({cur} / {lim})</span></div>"
                f"</div>"
            )
    else:
        quota_html = "<div class='muted'>尚无 monitor 数据。请先在配置页填入 token 并选择支持 monitor API 的厂商（如智谱）。</div>"

    # ── recent rows
    recent_rows_html = ""
    if recent:
        for r in recent[:50]:
            ts = html.escape(str(r.get("ts_text", "")))
            v = html.escape(str(r.get("vendor", "")))
            m = html.escape(str(r.get("model", "")))
            sc = r.get("status_code", 0)
            ttft = _fmt_latency(r.get("ttft_ms", 0))
            tps = r.get("tps_mean", 0) or 0
            inp = _fmt_tokens(r.get("input_tokens", 0))
            outp = _fmt_tokens(r.get("output_tokens", 0))
            tout = html.escape(str(r.get("timeout_type", "")) or "—")
            sc_cls = "sc-2xx" if 200 <= sc < 300 else "sc-4xx" if 400 <= sc < 500 else "sc-5xx" if 500 <= sc < 600 else "sc-0"
            recent_rows_html += (
                f"<tr><td class='small'>{ts}</td><td>{v}</td><td class='mono small'>{m}</td>"
                f"<td class='{sc_cls}'>{sc}</td><td>{ttft}</td><td>{tps:.1f}</td>"
                f"<td>{inp}</td><td>{outp}</td><td class='small'>{tout}</td></tr>"
            )
    else:
        recent_rows_html = "<tr><td colspan=9 class='muted'>暂无数据 — 把 IDE 的 base_url 改为 http://127.0.0.1:8080/<vendor>/ 即可开始</td></tr>"

    # ── daily sparkline (simple bars)
    daily_html = ""
    if daily:
        max_cnt = max((d.get("cnt", 0) for d in daily), default=1) or 1
        for d in daily:
            day = html.escape(str(d.get("day", "")))
            cnt = d.get("cnt", 0)
            h = max(2, int(cnt / max_cnt * 60))
            daily_html += (
                f"<div class='day'><div class='day-bar' style='height:{h}px' title='{day}: {cnt} calls'></div>"
                f"<div class='day-label'>{day[5:]}</div></div>"
            )

    token_status = "<span class='ok'>✓ Token 已配置</span>" if has_token else "<span class='warn'>⚠ 未配置 Token，<a href='/__ledger__/settings'>去配置</a></span>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>llm-api-ledger · 本地账单</title>
<style>
:root {{
  --bg:#0d1117; --panel:#161b22; --panel-2:#1c2128; --line:#30363d;
  --text:#e6edf3; --muted:#7d8590; --accent:#58a6ff; --accent-2:#3fb950;
  --warn:#d29922; --danger:#f85149;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text);
  font-family:'JetBrains Mono','SF Mono',Menlo,Consolas,monospace;
  font-size:13px; padding:24px; line-height:1.5; }}
h1 {{ font-size:18px; font-weight:600; margin-bottom:4px; }}
h2 {{ font-size:14px; font-weight:600; color:var(--muted); margin:24px 0 10px;
  text-transform:uppercase; letter-spacing:0.5px; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.header {{ display:flex; justify-content:space-between; align-items:flex-start;
  flex-wrap:wrap; gap:12px; margin-bottom:20px; }}
.header .meta {{ color:var(--muted); font-size:12px; }}
.header .meta .vp {{ color:var(--accent); }}
.nav {{ display:flex; gap:14px; align-items:center; font-size:12px; }}
.nav a {{ color:var(--muted); }}
.nav a.active {{ color:var(--text); }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-bottom:16px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:14px; }}
.card .label {{ color:var(--muted); font-size:11px; text-transform:uppercase;
  letter-spacing:0.5px; margin-bottom:6px; }}
.card .value {{ font-size:20px; font-weight:600; }}
.card .sub {{ color:var(--muted); font-size:11px; margin-top:4px; }}
.row {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px; }}
@media (max-width:780px) {{ .row {{ grid-template-columns:1fr; }} }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:14px; }}
.panel h3 {{ font-size:12px; color:var(--muted); text-transform:uppercase;
  letter-spacing:0.5px; margin-bottom:10px; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
th,td {{ padding:6px 8px; text-align:left; border-bottom:1px solid var(--line); }}
th {{ color:var(--muted); font-weight:500; font-size:11px;
  text-transform:uppercase; letter-spacing:0.5px; }}
td.mono {{ font-family:inherit; }}
td.small, .small {{ font-size:11px; }}
.muted {{ color:var(--muted); }}
.sc-2xx {{ color:var(--accent-2); }}
.sc-4xx {{ color:var(--warn); }}
.sc-5xx {{ color:var(--danger); }}
.sc-0 {{ color:var(--muted); }}
.bar {{ height:8px; border-radius:2px; background:var(--accent); min-width:2px; }}
.bar.sc-2xx {{ background:var(--accent-2); }}
.bar.sc-4xx {{ background:var(--warn); }}
.bar.sc-5xx {{ background:var(--danger); }}
.ok {{ color:var(--accent-2); }}
.warn {{ color:var(--warn); }}
.sparkline {{ display:flex; align-items:flex-end; gap:2px; height:80px; padding:8px 0; overflow-x:auto; }}
.day {{ display:flex; flex-direction:column; align-items:center; min-width:18px; }}
.day-bar {{ width:10px; background:var(--accent); border-radius:2px 2px 0 0; }}
.day-label {{ font-size:9px; color:var(--muted); margin-top:3px; transform:rotate(-60deg); transform-origin:center; white-space:nowrap; }}
.quota-card {{ background:var(--panel-2); border:1px solid var(--line); border-radius:6px; padding:10px; margin-bottom:8px; }}
.quota-head {{ display:flex; justify-content:space-between; margin-bottom:6px; }}
.quota-head .ptype {{ font-weight:600; }}
.quota-bar-bg {{ height:10px; background:var(--bg); border-radius:5px; overflow:hidden; }}
.quota-bar {{ height:100%; border-radius:5px; }}
.q-low {{ background:var(--accent-2); }}
.q-mid {{ background:var(--warn); }}
.q-high {{ background:var(--danger); }}
.quota-foot {{ font-size:11px; margin-top:4px; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>llm-api-ledger · 本地账单</h1>
    <div class="meta">
      厂商: <span class="vp">{html.escape(vendor_label)}</span> ·
      套餐: <span class="vp">{html.escape(plan_label)}</span> ·
      监听: <span class="vp">127.0.0.1:{cfg.get('listen_port', 8080)}</span> ·
      {token_status}
    </div>
  </div>
  <div class="nav">
    <a href="/__ledger__" class="active">账单</a>
    <a href="/__ledger__/settings">配置</a>
    <a href="/__ledger__/export">导出 PR</a>
    <a href="/__ledger__/api/stats" target="_blank">JSON</a>
  </div>
</div>

<div class="grid">
  <div class="card">
    <div class="label">今日输入</div>
    <div class="value">{_fmt_tokens(today_in)}</div>
    <div class="sub">tokens</div>
  </div>
  <div class="card">
    <div class="label">今日输出</div>
    <div class="value">{_fmt_tokens(today_out)}</div>
    <div class="sub">tokens</div>
  </div>
  <div class="card">
    <div class="label">30 天缓存命中</div>
    <div class="value">{_fmt_pct(cache_hit)}</div>
    <div class="sub">cache_read / (input+cc+cr)</div>
  </div>
  <div class="card">
    <div class="label">30 天平均 TTFT</div>
    <div class="value">{_fmt_latency(total.get('attft', 0))}</div>
    <div class="sub">首字延迟</div>
  </div>
  <div class="card">
    <div class="label">30 天平均延迟</div>
    <div class="value">{_fmt_latency(total.get('alat', 0))}</div>
    <div class="sub">总延迟</div>
  </div>
  <div class="card">
    <div class="label">30 天平均 TPS</div>
    <div class="value">{(total.get('atps', 0) or 0):.1f}</div>
    <div class="sub">tokens / second</div>
  </div>
</div>

<h2>厂商声称额度（monitor API · 三周期）</h2>
{quota_html}

<h2>30 天调用次数</h2>
<div class="panel">
  <div class="sparkline">{daily_html if daily else '<div class="muted">暂无数据</div>'}</div>
</div>

<div class="row">
  <div class="panel">
    <h3>状态码分布</h3>
    <table>
      <thead><tr><th>状态码</th><th>次数</th><th style="width:40%">分布</th></tr></thead>
      <tbody>{status_rows_html}</tbody>
    </table>
  </div>
  <div class="panel">
    <h3>超时类型分布（四分法）</h3>
    <table>
      <thead><tr><th>类型</th><th>次数</th></tr></thead>
      <tbody>{timeout_rows_html}</tbody>
    </table>
  </div>
</div>

<h2>各厂商用量</h2>
<div class="panel">
  <table>
    <thead><tr><th>厂商</th><th>请求数</th><th>输入</th><th>输出</th></tr></thead>
    <tbody>{vendor_rows_html}</tbody>
  </table>
</div>

<h2>最近 50 次请求</h2>
<div class="panel" style="overflow-x:auto">
  <table>
    <thead><tr>
      <th>时间</th><th>厂商</th><th>模型</th><th>状态</th>
      <th>TTFT</th><th>TPS</th><th>输入</th><th>输出</th><th>超时</th>
    </tr></thead>
    <tbody>{recent_rows_html}</tbody>
  </table>
</div>

</body>
</html>
"""
