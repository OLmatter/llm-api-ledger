"""
Export page — per-key data bundle export.

CSS: from base.css. JS: standalone <script>.
"""

from __future__ import annotations

import html
from typing import Any

from ._base import page_shell, topbar


def render(keys: list[dict[str, Any]], selected_key: dict[str, Any] | None) -> str:
    key_options = '<option value="0">\u5168\u90e8 Key\uff08\u805a\u5408\uff09</option>'
    for k in keys:
        kid = k["id"]
        label = html.escape(k.get("label", ""))
        sel = "selected" if selected_key and selected_key.get("id") == kid else ""
        key_options += f'<option value="{kid}" {sel}>{label}</option>'

    cur_label = html.escape(selected_key.get("label", "\u5168\u90e8 Key")) if selected_key else "\u5168\u90e8 Key"
    cur_vendor = html.escape(selected_key.get("vendor", "")) if selected_key else ""
    cur_plan = html.escape(selected_key.get("plan", "")) if selected_key else ""

    body = f"""
{topbar("export")}
<div class="body">
  <div class="page-title">\u5bfc\u51fa\u8131\u654f\u6570\u636e\u5305</div>
  <div class="page-sub">\u628a\u672c\u5730\u6838\u8d26\u6570\u636e\u6253\u5305\u6210 PR \u5305\u3002\u53ef\u6309\u5355\u4e2a key \u6216\u5168\u90e8\u805a\u5408\u5bfc\u51fa\u3002</div>

  <div class="privacy">
    <div class="privacy-title">\u2713 \u9690\u79c1\u4fdd\u62a4</div>
    <strong>\u5305\u542b</strong>\uff1a\u805a\u5408\u6307\u6807\uff08TTFT/TPS \u5206\u5e03\u3001\u72b6\u6001\u7801\u7edf\u8ba1\u3001\u8d85\u65f6\u7387\u3001\u7f13\u5b58\u547d\u4e2d\u7387\u3001monitor \u5feb\u7167\uff09<br>
    <strong>\u4e0d\u5305\u542b</strong>\uff1aPrompt \u5185\u5bb9\u3001\u4ee3\u7801\u4e0a\u4e0b\u6587\u3001API key\u3001\u5b8c\u6574 token\uff08\u53ea\u7559\u540e 4 \u4f4d\uff09
  </div>

  <div class="meta-row">
    <span class="meta-key">\u5f53\u524d:</span><span class="meta-val">{cur_label}</span>
    <span class="meta-key">\xb7 \u5382\u5546:</span><span class="meta-val">{cur_vendor}</span>
    <span class="meta-key">\xb7 \u5957\u9910:</span><span class="meta-val">{cur_plan}</span>
  </div>

  <div class="card" style="margin-bottom:16px">
    <div class="field">
      <label class="field-label">\u9009\u62e9 Key</label>
      <select id="keySelect" class="field-input">{key_options}</select>
    </div>
    <div class="field">
      <label class="field-label">\u65f6\u95f4\u7a97\uff08\u5929\uff09</label>
      <input id="days" type="number" class="field-input" value="7" min="1" max="90" style="width:140px">
    </div>
    <button class="btn btn-primary" id="generateBtn">\u751f\u6210\u6570\u636e\u5305</button>
  </div>

  <div class="result-card" id="result">
    <div class="result-title">JSON \u6570\u636e\u5305</div>
    <textarea id="jsonOut" readonly></textarea>
    <div class="result-actions">
      <a id="downloadLink" href="#" download="ledger-export.json"><button class="btn btn-secondary">\v \u4e0b\u8f7d JSON</button></a>
      <button class="btn btn-secondary" id="copyJsonBtn">Copy \u590d\u5236 JSON</button>
    </div>
    <div class="result-title">PR \u63cf\u8ff0\uff08Markdown\uff09</div>
    <textarea id="mdOut" readonly style="height:140px"></textarea>
    <button class="btn btn-secondary" id="copyMdBtn" style="margin-top:8px">Copy \u590d\u5236 Markdown</button>
    <div class="msg" id="msg"></div>
  </div>
</div>

<script>
(function() {{
  var msgEl = document.getElementById('msg');

  function showMsg(text, ok) {{
    msgEl.textContent = text;
    msgEl.className = 'msg show ' + (ok ? 'ok' : 'err');
  }}

  document.getElementById('keySelect').addEventListener('change', function(e) {{
    var v = e.target.value;
    window.location.href = '/__ledger__/export' + (v && v !== '0' ? '?key=' + v : '');
  }});

  document.getElementById('generateBtn').addEventListener('click', function() {{
    var key = document.getElementById('keySelect').value;
    var days = document.getElementById('days').value || 7;
    showMsg('\u751f\u6210\u4e2d...', true);

    fetch('/__ledger__/api/export?key=' + key + '&days=' + days)
      .then(function(r) {{ return r.json(); }})
      .then(function(data) {{
        if (!data.ok) throw new Error(data.error || 'failed');
        var json = JSON.stringify(data.bundle, null, 2);
        document.getElementById('jsonOut').value = json;
        document.getElementById('mdOut').value = data.pr_description || '';
        var blob = new Blob([json], {{type:'application/json'}});
        var url = URL.createObjectURL(blob);
        var dl = document.getElementById('downloadLink');
        dl.href = url;
        dl.download = data.filename || 'ledger-export.json';
        document.getElementById('result').style.display = '';
        showMsg('\u2713 ' + (data.filename || ''), true);
      }})
      .catch(function(err) {{ showMsg('\u5931\u8d25: ' + err.message, false); }});
  }});

  document.getElementById('copyJsonBtn').addEventListener('click', function() {{
    document.getElementById('jsonOut').select();
    document.execCommand('copy');
    alert('JSON \u5df2\u590d\u5236');
  }});
  document.getElementById('copyMdBtn').addEventListener('click', function() {{
    document.getElementById('mdOut').select();
    document.execCommand('copy');
    alert('Markdown \u5df2\u590d\u5236');
  }});
}})();
</script>"""

    return page_shell("Ledger \xb7 \u5bfc\u51fa", body)
