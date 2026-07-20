"""
Dashboard — mac minimal UI with key sidebar.

CSS: loaded from static/base.css (NO triple-quoted CSS).
JS: Chart.js from CDN, data injected via JSON <script> tag.
HTML body: built with plain string concatenation + .replace(), NOT f-string,
so JS curly braces don't conflict with Python format syntax.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from ._base import page_shell, topbar
from ..constants import CHART_JS_URL, RECENT_LIMIT


def _fmt_tokens(n):
    if not n: return "0"
    n = float(n)
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.2f}M"
    if n >= 1e3: return f"{n/1e3:.1f}K"
    return str(int(n))


def _fmt_latency(ms):
    if not ms: return "\u2014"
    return f"{ms/1000:.2f}s" if ms >= 1000 else f"{ms:.0f}ms"


def _fmt_pct(x, d=1):
    if x is None: return "\u2014"
    return f"{x*100:.{d}f}%"


def _sidebar(keys, selected_key):
    items = (
        '<a href="/__ledger__/" class="key-item ' + ("active" if not selected_key else "") + '">'
        '<div class="key-icon all">\u2211</div>'
        '<div class="key-meta"><div class="key-label">\u5168\u90e8 Key</div>'
        f'<div class="key-sub">{len(keys)} \u4e2a key</div></div></a>'
    )
    for k in keys:
        kid = k["id"]
        label = html.escape(k.get("label", ""))
        vendor = html.escape(k.get("vendor", ""))
        last4 = html.escape(k.get("token_last4", ""))
        active = "active" if selected_key and selected_key.get("id") == kid else ""
        inactive = "inactive" if not k.get("is_active") else ""
        icon_char = vendor[0].upper() if vendor else "?"
        items += (
            f'<a href="/__ledger__/?key={kid}" class="key-item {active} {inactive}">'
            f'<div class="key-icon {vendor}">{icon_char}</div>'
            f'<div class="key-meta"><div class="key-label">{label}</div>'
            f'<div class="key-sub">{vendor} \xb7 ***{last4}</div></div></a>'
        )
    return items


# ── JS is a PLAIN string (no f-string, no Python brace conflicts) ──
_JS_BLOCK = """<script src="__CHART_JS_URL__"></script>
<script id="chartData" type="application/json">__CHART_DATA__</script>
<script>
(function() {
  var data = JSON.parse(document.getElementById('chartData').textContent);
  Chart.defaults.font.family = "-apple-system,BlinkMacSystemFont,'SF Pro Text',sans-serif";
  Chart.defaults.font.size = 11;
  Chart.defaults.color = "#86868b";
  Chart.defaults.animation.duration = 400;

  var c1 = document.getElementById('hourlyChart');
  if (c1) new Chart(c1, {
    type: 'bar',
    data: { labels: data.hourly_labels, datasets: [
      { type:'bar', label:'\u8bf7\u6c42\u6570', data: data.hourly_calls,
        backgroundColor:'rgba(0,113,227,0.6)', borderRadius:3, yAxisID:'y' },
      { type:'line', label:'TTFT ms', data: data.hourly_ttft,
        borderColor:'#ff9500', backgroundColor:'rgba(255,149,0,0.1)',
        borderWidth:2, pointRadius:0, tension:0.35, yAxisID:'y1', fill:false }
    ]},
    options: { maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      plugins:{ legend:{display:true,position:'top',align:'end',labels:{boxWidth:8,boxHeight:8,padding:12}} },
      scales:{ x:{grid:{display:false},ticks:{maxRotation:0,autoSkipPadding:16}},
               y:{position:'left',grid:{color:'#ececf0'},beginAtZero:true},
               y1:{position:'right',grid:{display:false},beginAtZero:true} } }
  });

  var c2 = document.getElementById('timeoutChart');
  if (c2) new Chart(c2, {
    type: 'line',
    data: { labels: data.hourly_labels, datasets: [{
      label:'\u8d85\u65f6\u7387%', data: data.hourly_timeout,
      borderColor:'#ff3b30', backgroundColor:'rgba(255,59,48,0.12)',
      borderWidth:2, pointRadius:2, tension:0.3, fill:true
    }]},
    options: { maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{ x:{grid:{display:false},ticks:{maxRotation:0,autoSkipPadding:16}},
               y:{grid:{color:'#ececf0'},beginAtZero:true,ticks:{callback:function(v){return v+'%'}}} } }
  });

  var c3 = document.getElementById('dailyChart');
  if (c3) new Chart(c3, {
    type: 'bar',
    data: { labels: data.daily_labels, datasets: [
      { label:'\u8f93\u5165', data: data.daily_in, backgroundColor:'rgba(0,113,227,0.7)', stack:'t', borderRadius:3 },
      { label:'\u8f93\u51fa', data: data.daily_out, backgroundColor:'rgba(52,199,89,0.7)', stack:'t', borderRadius:3 }
    ]},
    options: { maintainAspectRatio:false,
      plugins:{legend:{display:true,position:'top',align:'end',labels:{boxWidth:8,boxHeight:8,padding:12}}},
      scales:{ x:{grid:{display:false},stacked:true},
               y:{grid:{color:'#ececf0'},stacked:true,beginAtZero:true,
                  ticks:{callback:function(v){return v>=1e6?(v/1e6).toFixed(1)+'M':v>=1e3?(v/1e3).toFixed(0)+'K':v}} } } }
  });
})();
</script>"""


def render(stats, cfg, hourly, daily, keys, selected_key):
    total = stats.get("total", {}) or {}
    today = stats.get("today", {}) or {}
    status_breakdown = stats.get("status_breakdown", []) or []
    timeout_breakdown = stats.get("timeout_breakdown", []) or []
    recent = stats.get("recent", []) or []
    quota = stats.get("quota", []) or []

    total_in = total.get("si", 0) or 0
    total_out = total.get("so", 0) or 0
    total_cc = total.get("scc", 0) or 0
    total_cr = total.get("scr", 0) or 0
    cache_total = total_in + total_cr + total_cc
    cache_hit = (total_cr / cache_total) if cache_total else 0
    today_in = today.get("si", 0) or 0
    today_out = today.get("so", 0) or 0
    today_count = today.get("cnt", 0) or 0
    listen_port = cfg.get("listen_port", 8080)
    view_title = html.escape(selected_key.get("label", "\u5168\u90e8 Key")) if selected_key else "\u5168\u90e8 Key"

    # Status chips
    status_chips = ""
    if status_breakdown:
        s_total = sum(r.get("cnt", 0) for r in status_breakdown) or 1
        for r in status_breakdown:
            sc = r.get("status_code", 0)
            cnt = r.get("cnt", 0)
            pct = cnt / s_total * 100
            cls = "good" if 200 <= sc < 300 else "warn" if 400 <= sc < 500 else "bad" if 500 <= sc < 600 else ""
            status_chips += f'<span class="chip {cls}"><span class="chip-num">{sc}</span><span class="chip-meta">{cnt} \xb7 {pct:.1f}%</span></span>'
    else:
        status_chips = '<span class="empty-hint">\u6682\u65e0\u6570\u636e</span>'

    # Timeout chips
    timeout_chips = ""
    if timeout_breakdown:
        for r in timeout_breakdown:
            t = html.escape(str(r.get("timeout_type", "")))
            cnt = r.get("cnt", 0)
            timeout_chips += f'<span class="chip bad"><span class="chip-num">{t}</span><span class="chip-meta">{cnt}</span></span>'
    else:
        timeout_chips = '<span class="empty-hint good">\u65e0\u8d85\u65f6 \u2713</span>'

    # Quota cards
    quota_html = ""
    if quota:
        seen = set()
        for q in quota:
            ptype = html.escape(str(q.get("period_type", "")))
            if ptype in seen:
                continue
            seen.add(ptype)
            pct = q.get("percentage", 0) or 0
            cur = _fmt_tokens(q.get("current_value", 0))
            lim = _fmt_tokens(q.get("limit_value", 0))
            ts = html.escape(str(q.get("ts_text", "")))[5:]
            bar_pct = min(pct * 100, 100)
            bar_cls = "low" if pct < 0.7 else "mid" if pct < 0.9 else "high"
            plabel = {"tokens_5h": "5 \u5c0f\u65f6\u7a97\u53e3", "tokens_weekly": "\u672c\u5468\u914d\u989d", "mcp_30d": "30 \u5929 MCP"}.get(ptype, ptype)
            quota_html += (
                f'<div class="quota-card">'
                f'<div class="quota-head"><span class="quota-label">{plabel}</span><span class="quota-ts">{ts}</span></div>'
                f'<div class="quota-value">{pct*100:.1f}<span class="quota-unit">%</span></div>'
                f'<div class="quota-bar"><div class="quota-fill {bar_cls}" style="width:{bar_pct}%"></div></div>'
                f'<div class="quota-foot">{cur} / {lim}</div></div>'
            )
    else:
        quota_html = '<div class="empty-hint">\u5c1a\u65e0 monitor \u6570\u636e\u3002\u5728\u914d\u7f6e\u9875\u6dfb\u52a0 key\u3002</div>'

    # Recent rows
    recent_rows = ""
    if recent:
        for r in recent[:RECENT_LIMIT]:
            ts = html.escape(str(r.get("ts_text", "")))[5:]
            v = html.escape(str(r.get("vendor", "")))
            m = html.escape(str(r.get("model", "")))
            sc = r.get("status_code", 0)
            ttft = _fmt_latency(r.get("ttft_ms", 0))
            tps = r.get("tps_mean", 0) or 0
            inp = _fmt_tokens(r.get("input_tokens", 0))
            outp = _fmt_tokens(r.get("output_tokens", 0))
            tout = html.escape(str(r.get("timeout_type", "")) or "\u2014")
            sc_cls = "good" if 200 <= sc < 300 else "warn" if 400 <= sc < 500 else "bad" if 500 <= sc < 600 else "muted"
            recent_rows += (
                f'<tr><td class="muted">{ts}</td><td>{v}</td><td class="mono">{m}</td>'
                f'<td class="status {sc_cls}">{sc}</td><td>{ttft}</td><td>{tps:.1f}</td>'
                f'<td class="muted">{inp}</td><td class="muted">{outp}</td>'
                f'<td class="muted small">{tout}</td></tr>'
            )
    else:
        hint_vendor = selected_key.get("vendor", "zhipu") if selected_key else "zhipu"
        hint_label = selected_key.get("label", "") if selected_key else ""
        recent_rows = (
            f'<tr><td colspan="9" class="empty-row">\u6682\u65e0\u8bf7\u6c42 \u2014 '
            f'\u5728 IDE \u91cc\u628a base_url \u6539\u4e3a '
            f'<code>http://127.0.0.1:{listen_port}/{hint_vendor}/{hint_label}</code></td></tr>'
        )

    # Chart data as JSON
    chart_data = json.dumps({
        "hourly_labels": [h["hour_label"] for h in hourly],
        "hourly_calls": [h["count"] for h in hourly],
        "hourly_ttft": [h["avg_ttft"] for h in hourly],
        "hourly_timeout": [round(h["timeout_rate"] * 100, 1) for h in hourly],
        "daily_labels": [d["day"][5:] for d in daily],
        "daily_in": [d["input_tokens"] for d in daily],
        "daily_out": [d["output_tokens"] for d in daily],
    }, ensure_ascii=False)

    sidebar_html = _sidebar(keys, selected_key)
    tb = topbar("dashboard")

    # Build HTML body with plain string concatenation (no f-string on JS parts)
    body_parts = [
        '<div class="layout">',
        '  <aside class="sidebar">',
        '    <div class="sidebar-brand">',
        '      <div class="brand-logo">L</div>',
        '      <div><div class="brand-name">Ledger</div><div class="brand-sub">\u672c\u5730\u6838\u8d26</div></div>',
        '    </div>',
        f'    <div class="sidebar-section">Key \u5217\u8868</div>',
        f'    {sidebar_html}',
        '    <div class="sidebar-add"><a href="/__ledger__/settings">+ \u6dfb\u52a0 Key</a></div>',
        '  </aside>',
        '  <main class="main">',
        tb,
        f'    <div class="page-head"><div class="view-title">{view_title}</div></div>',
        # Hero cards
        '    <div class="hero-grid">',
        f'      <div class="card"><div class="card-label">\u4eca\u65e5\u8bf7\u6c42</div><div class="card-value">{today_count}<span class="card-unit">\u6b21</span></div><div class="card-sub">\u5165 {_fmt_tokens(today_in)} \xb7 \u51fa {_fmt_tokens(today_out)}</div></div>',
        f'      <div class="card"><div class="card-label">30 \u5929\u8f93\u5165</div><div class="card-value">{_fmt_tokens(total_in)}</div><div class="card-sub">tokens</div></div>',
        f'      <div class="card"><div class="card-label">30 \u5929\u8f93\u51fa</div><div class="card-value">{_fmt_tokens(total_out)}</div><div class="card-sub">tokens</div></div>',
        f'      <div class="card"><div class="card-label">\u7f13\u5b58\u547d\u4e2d</div><div class="card-value">{_fmt_pct(cache_hit)}</div><div class="card-sub">\u771f\u901a\u9053\u624d\u4f1a\u9ad8</div></div>',
        f'      <div class="card"><div class="card-label">\u5e73\u5747 TTFT</div><div class="card-value">{_fmt_latency(total.get("attft",0))}</div><div class="card-sub">\u9996\u5b57\u5ef6\u8fdf</div></div>',
        f'      <div class="card"><div class="card-label">\u5e73\u5747\u5ef6\u8fdf</div><div class="card-value">{_fmt_latency(total.get("alat",0))}</div><div class="card-sub">\u603b\u65f6\u957f</div></div>',
        '    </div>',
        # 24h charts
        '    <div class="section">',
        '      <div class="section-head"><div class="section-title">\u6700\u8fd1 24 \u5c0f\u65f6</div><div class="section-sub">\u6bcf\u5c0f\u65f6\u805a\u5408</div></div>',
        '      <div class="chart-grid">',
        '        <div class="chart-card"><div class="chart-title">\u8bf7\u6c42\u6570 & TTFT</div><div class="chart-sub">\u67f1=\u8bf7\u6c42\u6570 \xb7 \u7ebf=TTFT ms</div><div class="chart-wrap"><canvas id="hourlyChart"></canvas></div></div>',
        '        <div class="chart-card"><div class="chart-title">\u8d85\u65f6\u7387</div><div class="chart-sub">\u7a81\u589e = \u9634\u9669\u9650\u6d41</div><div class="chart-wrap"><canvas id="timeoutChart"></canvas></div></div>',
        '      </div>',
        '    </div>',
        # 7d chart
        '    <div class="section">',
        '      <div class="section-head"><div class="section-title">\u6700\u8fd1 7 \u5929</div><div class="section-sub">\u6309\u5929\u805a\u5408</div></div>',
        '      <div class="chart-card"><div class="chart-title">\u6bcf\u65e5 Token \u7528\u91cf</div><div class="chart-sub">\u5165 vs \u51fa\uff08\u5806\u53e0\uff09</div><div class="chart-wrap"><canvas id="dailyChart"></canvas></div></div>',
        '    </div>',
        # Quota
        '    <div class="section">',
        '      <div class="section-head"><div class="section-title">\u5382\u5546\u58f0\u79f0\u989d\u5ea6</div><div class="section-sub">monitor API \xb7 \u4e09\u65b9\u4ea4\u53c9\u9a8c\u8bc1</div></div>',
        f'      <div class="quota-grid">{quota_html}</div>',
        '    </div>',
        # Stability
        '    <div class="section">',
        '      <div class="section-head"><div class="section-title">\u7a33\u5b9a\u6027\u5206\u5e03</div><div class="section-sub">30 \u5929</div></div>',
        '      <div class="chart-grid">',
        f'        <div class="chart-card"><div class="chart-title">\u72b6\u6001\u7801</div><div class="chart-sub">402=\u8017\u5c3d \xb7 429=\u9650\u6d41 \xb7 5xx=\u9519</div><div class="chip-row" style="margin-top:6px">{status_chips}</div></div>',
        f'        <div class="chart-card"><div class="chart-title">\u8d85\u65f6\u7c7b\u578b</div><div class="chart-sub">\u56db\u5206\u6cd5</div><div class="chip-row" style="margin-top:6px">{timeout_chips}</div></div>',
        '      </div>',
        '    </div>',
        # Recent requests
        '    <div class="section">',
        f'      <div class="section-head"><div class="section-title">\u6700\u8fd1 {RECENT_LIMIT} \u6b21\u8bf7\u6c42</div><div class="section-sub">\u6700\u65b0\u5728\u524d</div></div>',
        '      <div class="table-card" style="overflow-x:auto">',
        '        <table><thead><tr><th>\u65f6\u95f4</th><th>\u5382\u5546</th><th>\u6a21\u578b</th><th>\u72b6\u6001</th><th>TTFT</th><th>TPS</th><th>\u5165</th><th>\u51fa</th><th>\u8d85\u65f6</th></tr></thead>',
        f'        <tbody>{recent_rows}</tbody></table>',
        '      </div>',
        '    </div>',
        # Footer
        '    <div class="foot">',
        '      <div>\u6570\u636e\u5168\u90e8\u5b58\u672c\u5730 SQLite \xb7 <a href="/__ledger__/export">\u5bfc\u51fa PR \u5305</a></div>',
        '      <div>v0.1.0-alpha \xb7 <a href="https://github.com/OLmatter/llm-api-ledger" target="_blank">GitHub</a></div>',
        '    </div>',
        '  </main>',
        '</div>',
    ]
    body_html = "\n".join(body_parts)

    # JS block: plain string with __PLACEHOLDER__ replacement (no f-string)
    js_html = _JS_BLOCK.replace("__CHART_JS_URL__", CHART_JS_URL).replace("__CHART_DATA__", chart_data)

    full_body = body_html + "\n" + js_html
    return page_shell("Ledger \xb7 \u672c\u5730\u8d26\u5355", full_body)
