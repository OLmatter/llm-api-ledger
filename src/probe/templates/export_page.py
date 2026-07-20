"""
Export page HTML.

Route: /__ledger__/export

Lets the user pick a time window (default: last 7 days) and either:
  - Download the JSON bundle (for manual PR / TG submission)
  - Copy a generated Markdown PR description
"""

from __future__ import annotations

from typing import Any


def render(cfg: dict[str, Any]) -> str:
    vendor = cfg.get("vendor", "")
    plan = cfg.get("plan", "")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>llm-api-ledger · 导出 PR</title>
<style>
:root {{
  --bg:#0d1117; --panel:#161b22; --line:#30363d;
  --text:#e6edf3; --muted:#7d8590; --accent:#58a6ff; --accent-2:#3fb950;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text);
  font-family:'JetBrains Mono','SF Mono',Menlo,Consolas,monospace;
  font-size:13px; padding:24px; line-height:1.5; }}
h1 {{ font-size:18px; margin-bottom:4px; }}
.nav {{ display:flex; gap:14px; margin-bottom:20px; font-size:12px; }}
.nav a {{ color:var(--muted); }}
.nav a.active {{ color:var(--text); }}
.meta {{ color:var(--muted); font-size:12px; margin-bottom:20px; }}
.form {{ background:var(--panel); border:1px solid var(--line);
  border-radius:6px; padding:18px; max-width:640px; margin-bottom:20px; }}
.field {{ margin-bottom:14px; }}
.field label {{ display:block; color:var(--muted); font-size:11px;
  text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }}
.field input, .field select {{ background:#0d1117; color:var(--text);
  border:1px solid var(--line); border-radius:4px; padding:8px 10px;
  font-family:inherit; font-size:13px; }}
.field input[type=number] {{ width:120px; }}
button {{ background:var(--accent); color:#0d1117; border:none; border-radius:4px;
  padding:8px 16px; font-family:inherit; font-size:13px; font-weight:600;
  cursor:pointer; margin-right:8px; }}
button:hover {{ background:#79b8ff; }}
button.secondary {{ background:transparent; color:var(--accent);
  border:1px solid var(--accent); }}
.result {{ background:var(--panel); border:1px solid var(--line);
  border-radius:6px; padding:14px; max-width:640px; }}
.result h3 {{ color:var(--muted); font-size:11px;
  text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }}
.result textarea {{ width:100%; height:200px; background:#0d1117;
  color:var(--text); border:1px solid var(--line); border-radius:4px;
  padding:8px; font-family:inherit; font-size:12px; }}
.privacy {{ background:rgba(63,185,80,0.06); border:1px solid var(--accent-2);
  border-radius:4px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:var(--accent-2); }}
.msg {{ margin-top:10px; font-size:12px; }}
.ok {{ color:var(--accent-2); }}
</style>
</head>
<body>
<div class="nav">
  <a href="/__ledger__">账单</a>
  <a href="/__ledger__/settings">配置</a>
  <a href="/__ledger__/export" class="active">导出 PR</a>
  <a href="/__ledger__/api/stats" target="_blank">JSON</a>
</div>
<h1>导出脱敏数据包</h1>
<div class="meta">厂商: <code>{vendor}</code> · 套餐: <code>{plan}</code></div>

<div class="privacy">
  <strong>隐私保护</strong><br>
  导出包含：聚合指标（TTFT/TPS 分布、状态码统计、超时率、缓存命中率、厂商 monitor 快照）。<br>
  <strong>不</strong>包含：Prompt 内容、代码上下文、API key、完整 token（只留后 4 位）。
</div>

<form class="form" id="exportForm">
  <div class="field">
    <label for="days">时间窗（最近多少天）</label>
    <input id="days" type="number" value="7" min="1" max="90">
  </div>
  <button type="submit">生成数据包</button>
</form>

<div class="result" id="result" style="display:none">
  <h3>JSON 数据包（点击下载或复制）</h3>
  <textarea id="jsonOut" readonly></textarea>
  <div style="margin-top:8px">
    <a id="downloadLink" href="#" download="ledger-export.json">
      <button type="button" class="secondary">⬇ 下载 JSON</button>
    </a>
    <button type="button" class="secondary" id="copyJsonBtn">📋 复制 JSON</button>
  </div>
  <h3 style="margin-top:18px">PR 描述（Markdown）</h3>
  <textarea id="mdOut" readonly style="height:160px"></textarea>
  <button type="button" class="secondary" id="copyMdBtn" style="margin-top:8px">📋 复制 Markdown</button>
  <div id="msg" class="msg"></div>
</div>

<script>
document.getElementById('exportForm').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const days = parseInt(document.getElementById('days').value, 10) || 7;
  const msg = document.getElementById('msg');
  msg.className = 'msg';
  msg.textContent = '生成中...';
  try {{
    const resp = await fetch('/__ledger__/api/export?days=' + days);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || resp.status);
    const json = JSON.stringify(data.bundle, null, 2);
    document.getElementById('jsonOut').value = json;
    document.getElementById('mdOut').value = data.pr_description || '';
    const blob = new Blob([json], {{type:'application/json'}});
    const url = URL.createObjectURL(blob);
    const dl = document.getElementById('downloadLink');
    dl.href = url;
    dl.download = data.filename || 'ledger-export.json';
    document.getElementById('result').style.display = '';
    msg.className = 'msg ok';
    msg.textContent = '✓ 生成完毕，文件名: ' + (data.filename || '');
  }} catch (err) {{
    msg.className = 'msg';
    msg.style.color = 'var(--danger)';
    msg.textContent = '失败: ' + err;
  }}
}});

document.getElementById('copyJsonBtn').addEventListener('click', () => {{
  document.getElementById('jsonOut').select();
  document.execCommand('copy');
  alert('JSON 已复制');
}});
document.getElementById('copyMdBtn').addEventListener('click', () => {{
  document.getElementById('mdOut').select();
  document.execCommand('copy');
  alert('Markdown 已复制');
}});
</script>
</body>
</html>
"""
