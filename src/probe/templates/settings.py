"""
Settings page HTML.

Route: /__ledger__/settings

Form fields:
  - token (password box — value is read into JS then POSTed; server
    stores via OS keychain, never echoes back the plaintext on re-render)
  - vendor (select; cascades plan options + upstream_url + monitor_url)
  - plan (select; populated by vendor)
  - listen_port (number; read-only — port change requires restart)
  - monitor_interval_s (number)
  - opt_in_upload (checkbox)
  - relay custom: upstream_url override (only when vendor=relay)

On submit: POST /__ledger__/api/settings with JSON; server updates
config + keychain; reloads dashboard.
"""

from __future__ import annotations

import html
import json
from typing import Any

from .. import config_store


def render(cfg: dict[str, Any], has_token: bool) -> str:
    vendors_json = json.dumps(
        {
            k: {
                "label": v["label"],
                "url_prefix": v["url_prefix"],
                "upstream_default": v.get("upstream_default", ""),
                "monitor_url_default": v.get("monitor_url_default", ""),
                "plans": v.get("plans", []),
            }
            for k, v in config_store.VENDORS.items()
        },
        ensure_ascii=False,
    )
    current_vendor = html.escape(cfg.get("vendor", "zhipu"))
    current_plan = html.escape(cfg.get("plan", ""))
    current_upstream = html.escape(cfg.get("upstream_url", ""))
    current_monitor = html.escape(cfg.get("monitor_url", ""))
    listen_port = cfg.get("listen_port", 8080)
    monitor_interval = cfg.get("monitor_interval_s", 300)
    opt_in = "checked" if cfg.get("opt_in_upload", True) else ""
    user_hash = html.escape(cfg.get("user_hash", ""))
    relay_plan_label = html.escape(cfg.get("relay_plan_label", ""))

    token_state = (
        '<span class="ok">✓ Token 已配置（存储在系统 keychain）</span>'
        if has_token
        else '<span class="warn">⚠ 未配置 Token</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>llm-api-ledger · 配置</title>
<style>
:root {{
  --bg:#0d1117; --panel:#161b22; --line:#30363d;
  --text:#e6edf3; --muted:#7d8590; --accent:#58a6ff;
  --accent-2:#3fb950; --warn:#d29922; --danger:#f85149;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text);
  font-family:'JetBrains Mono','SF Mono',Menlo,Consolas,monospace;
  font-size:13px; padding:24px; line-height:1.5; }}
h1 {{ font-size:18px; font-weight:600; margin-bottom:4px; }}
a {{ color:var(--accent); }}
.nav {{ display:flex; gap:14px; align-items:center; font-size:12px; margin-bottom:20px; }}
.nav a {{ color:var(--muted); }}
.nav a.active {{ color:var(--text); }}
.meta {{ color:var(--muted); font-size:12px; margin-bottom:20px; }}
.form {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:18px; max-width:640px; }}
.field {{ margin-bottom:16px; }}
.field label {{ display:block; color:var(--muted); font-size:11px;
  text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }}
.field input, .field select {{ width:100%; background:#0d1117; color:var(--text);
  border:1px solid var(--line); border-radius:4px; padding:8px 10px;
  font-family:inherit; font-size:13px; }}
.field input[type=number] {{ width:140px; }}
.field .hint {{ font-size:11px; color:var(--muted); margin-top:4px; }}
.field .hint.danger {{ color:var(--danger); }}
.checkbox-field {{ display:flex; align-items:center; gap:8px; }}
.checkbox-field input {{ width:auto; }}
.checkbox-field label {{ color:var(--text); text-transform:none; letter-spacing:0; font-size:13px; }}
button.save {{ background:var(--accent); color:#0d1117; border:none; border-radius:4px;
  padding:10px 20px; font-family:inherit; font-size:13px; font-weight:600;
  cursor:pointer; margin-right:8px; }}
button.save:hover {{ background:#79b8ff; }}
button.danger {{ background:transparent; color:var(--danger); border:1px solid var(--danger); border-radius:4px;
  padding:10px 20px; font-family:inherit; font-size:13px; cursor:pointer; }}
.ok {{ color:var(--accent-2); }}
.warn {{ color:var(--warn); }}
.msg {{ margin-top:12px; padding:8px 12px; border-radius:4px; font-size:12px; display:none; }}
.msg.ok-show {{ display:block; background:rgba(63,185,80,0.1); color:var(--accent-2); border:1px solid var(--accent-2); }}
.msg.err-show {{ display:block; background:rgba(248,81,73,0.1); color:var(--danger); border:1px solid var(--danger); }}
.token-warning {{ background:rgba(210,153,34,0.08); border:1px solid var(--warn);
  border-radius:4px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:var(--warn); }}
.token-warning strong {{ color:var(--warn); }}
</style>
</head>
<body>
<div class="nav">
  <a href="/__ledger__">账单</a>
  <a href="/__ledger__/settings" class="active">配置</a>
  <a href="/__ledger__/export">导出 PR</a>
  <a href="/__ledger__/api/stats" target="_blank">JSON</a>
</div>
<h1>llm-api-ledger · 配置</h1>
<div class="meta">Token 状态: {token_state} · user_hash: <code>{user_hash or '(未生成)'}</code></div>

<div class="token-warning">
  <strong>⚠ Token 安全提示</strong><br>
  Token 存储在系统 keychain（Windows Credential Manager / macOS Keychain / Linux Secret Service），
  绝不写入磁盘明文、不进日志、不上传。<br>
  <strong>不要</strong>在任何聊天、截图、GitHub issue、PR 里贴完整 token。
  如需共享数据，请用「导出 PR」功能（自动脱敏，只保留后 4 位）。
</div>

<form class="form" id="settingsForm">
  <div class="field">
    <label for="token">API Token（智谱即为 ANTHROPIC_AUTH_TOKEN）</label>
    <input id="token" name="token" type="password" placeholder="粘贴你的 token（不会显示明文）" autocomplete="off">
    <div class="hint">留空表示不修改现有 token。首次配置必须填。</div>
  </div>

  <div class="field">
    <label for="vendor">厂商</label>
    <select id="vendor" name="vendor">
      <!-- options populated by JS based on VENDORS -->
    </select>
    <div class="hint">不同厂商对应不同 base_url 前缀。改 IDE 的 base_url 时记得带上前缀。</div>
  </div>

  <div class="field">
    <label for="plan">套餐</label>
    <select id="plan" name="plan"></select>
  </div>

  <div class="field" id="relayLabelField" style="display:none">
    <label for="relay_plan_label">中转站套餐名（自定义）</label>
    <input id="relay_plan_label" name="relay_plan_label" type="text" value="{relay_plan_label}" placeholder="例: 某中转站 9.9 元套餐">
  </div>

  <div class="field">
    <label for="upstream_url">上游 URL</label>
    <input id="upstream_url" name="upstream_url" type="text" value="{current_upstream}">
    <div class="hint">选厂商时自动填，可手动改。探针会把 IDE 请求转发到这里。</div>
  </div>

  <div class="field">
    <label for="monitor_url">Monitor API URL（厂商额度查询）</label>
    <input id="monitor_url" name="monitor_url" type="text" value="{current_monitor}">
    <div class="hint">智谱/Z.ai 有此 API；DeepSeek/OpenAI/Anthropic 暂无，留空即可。</div>
  </div>

  <div class="field">
    <label for="listen_port">本地监听端口</label>
    <input id="listen_port" name="listen_port" type="number" value="{listen_port}" readonly>
    <div class="hint">改端口需重启探针。</div>
  </div>

  <div class="field">
    <label for="monitor_interval_s">Monitor 探查间隔（秒）</label>
    <input id="monitor_interval_s" name="monitor_interval_s" type="number" value="{monitor_interval}" min="60">
    <div class="hint">默认 300 秒（5 分钟）。低于 60 秒会被强制提到 60 秒。</div>
  </div>

  <div class="field checkbox-field">
    <input id="opt_in_upload" name="opt_in_upload" type="checkbox" {opt_in}>
    <label for="opt_in_upload">志愿上传脱敏数据（未来开放，目前仅本地）</label>
  </div>

  <button type="submit" class="save">保存配置</button>
  <button type="button" class="danger" id="clearTokenBtn">清除 Token</button>
  <div id="msg" class="msg"></div>
</form>

<script>
const VENDORS = {vendors_json};
const CURRENT_VENDOR = "{current_vendor}";
const CURRENT_PLAN = "{current_plan}";

function populateVendors() {{
  const sel = document.getElementById('vendor');
  sel.innerHTML = '';
  for (const [key, v] of Object.entries(VENDORS)) {{
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = v.label + '  (/' + v.url_prefix + '/)';
    if (key === CURRENT_VENDOR) opt.selected = true;
    sel.appendChild(opt);
  }}
}}
function populatePlans(vendorKey, selectedPlan) {{
  const v = VENDORS[vendorKey];
  const sel = document.getElementById('plan');
  sel.innerHTML = '';
  if (!v) return;
  if (!v.plans || v.plans.length === 0) {{
    const opt = document.createElement('option');
    opt.value = 'custom';
    opt.textContent = '自定义（在下方填中转站套餐名）';
    sel.appendChild(opt);
    document.getElementById('relayLabelField').style.display = '';
  }} else {{
    document.getElementById('relayLabelField').style.display = 'none';
    for (const p of v.plans) {{
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.label;
      if (p.id === selectedPlan) opt.selected = true;
      sel.appendChild(opt);
    }}
  }}
}}
function updateUpstreamDefaults(vendorKey) {{
  const v = VENDORS[vendorKey];
  if (!v) return;
  // Only auto-fill if the current value is empty or matches another vendor's default
  const up = document.getElementById('upstream_url');
  const mo = document.getElementById('monitor_url');
  if (!up.value || Object.values(VENDORS).some(x => x.upstream_default === up.value)) {{
    up.value = v.upstream_default || '';
  }}
  if (!mo.value || Object.values(VENDORS).some(x => x.monitor_url_default === mo.value)) {{
    mo.value = v.monitor_url_default || '';
  }}
}}

populateVendors();
populatePlans(CURRENT_VENDOR, CURRENT_PLAN);
updateUpstreamDefaults(CURRENT_VENDOR);

document.getElementById('vendor').addEventListener('change', (e) => {{
  populatePlans(e.target.value, '');
  updateUpstreamDefaults(e.target.value);
}});

document.getElementById('settingsForm').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const msg = document.getElementById('msg');
  msg.className = 'msg';
  const payload = {{
    vendor: document.getElementById('vendor').value,
    plan: document.getElementById('plan').value,
    upstream_url: document.getElementById('upstream_url').value,
    monitor_url: document.getElementById('monitor_url').value,
    monitor_interval_s: parseInt(document.getElementById('monitor_interval_s').value, 10),
    opt_in_upload: document.getElementById('opt_in_upload').checked,
    relay_plan_label: document.getElementById('relay_plan_label').value,
  }};
  const token = document.getElementById('token').value;
  if (token) payload.token = token;
  try {{
    const resp = await fetch('/__ledger__/api/settings', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
    }});
    const data = await resp.json();
    if (resp.ok && data.ok) {{
      msg.className = 'msg ok-show';
      msg.textContent = '✓ 已保存。Token 已存入 keychain。';
      document.getElementById('token').value = '';
      // reload after a moment to refresh user_hash display
      setTimeout(() => window.location.reload(), 1200);
    }} else {{
      msg.className = 'msg err-show';
      msg.textContent = '保存失败: ' + (data.error || resp.status);
    }}
  }} catch (err) {{
    msg.className = 'msg err-show';
    msg.textContent = '请求失败: ' + err;
  }}
}});

document.getElementById('clearTokenBtn').addEventListener('click', async () => {{
  if (!confirm('确认清除 keychain 里的 token？清除后探针无法调 monitor API。')) return;
  try {{
    const resp = await fetch('/__ledger__/api/token', {{method: 'DELETE'}});
    const data = await resp.json();
    if (resp.ok && data.ok) {{
      document.getElementById('msg').className = 'msg ok-show';
      document.getElementById('msg').textContent = '✓ Token 已清除';
      setTimeout(() => window.location.reload(), 1200);
    }} else {{
      document.getElementById('msg').className = 'msg err-show';
      document.getElementById('msg').textContent = '清除失败: ' + (data.error || resp.status);
    }}
  }} catch (err) {{
    document.getElementById('msg').className = 'msg err-show';
    document.getElementById('msg').textContent = '请求失败: ' + err;
  }}
}});
</script>
</body>
</html>
"""
