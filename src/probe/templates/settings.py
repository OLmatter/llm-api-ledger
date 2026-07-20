"""
Settings page — key list + add/edit modal.

CSS: from base.css. JS: standalone <script>, no f-string escape.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from ._base import page_shell, topbar
from .. import config_store


def render(keys: list[dict[str, Any]], cfg: dict[str, Any]) -> str:
    vendors_json = json.dumps(
        {k: {"label": v["label"], "url_prefix": v["url_prefix"],
             "upstream_default": v.get("upstream_default", ""),
             "monitor_url_default": v.get("monitor_url_default", ""),
             "plans": v.get("plans", [])}
         for k, v in config_store.VENDORS.items()},
        ensure_ascii=False,
    )

    key_cards = ""
    if keys:
        for k in keys:
            kid = k["id"]
            label = html.escape(k.get("label", ""))
            vendor = html.escape(k.get("vendor", ""))
            plan_id = html.escape(k.get("plan", ""))
            last4 = html.escape(k.get("token_last4", ""))
            upstream = html.escape(k.get("upstream_url", ""))
            active = k.get("is_active", 1)
            created = k.get("created_at", 0)
            last_used = k.get("last_used_at", 0)
            created_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "\u2014"
            last_used_str = datetime.fromtimestamp(last_used).strftime("%m-%d %H:%M") if last_used else "\u672a\u4f7f\u7528"
            active_dot = '<span class="dot active"></span>' if active else '<span class="dot inactive"></span>'
            vinfo = config_store.VENDORS.get(vendor, {})
            plan_label = plan_id
            for p in vinfo.get("plans", []):
                if p.get("id") == plan_id:
                    plan_label = html.escape(p.get("label", plan_id))
                    break
            vendor_label = html.escape(vinfo.get("label", vendor))
            key_data = html.escape(json.dumps(k, ensure_ascii=False))
            url_hint = f"http://127.0.0.1:{cfg.get('listen_port', 8080)}/{vinfo.get('url_prefix', vendor)}/{k.get('label', '')}"

            key_cards += f"""
            <div class="key-card" data-key-id="{kid}">
              <div class="key-card-head">
                <div class="key-card-icon {vendor}">{vendor[0].upper() if vendor else "?"}</div>
                <div class="key-card-title">
                  <div class="key-card-label">{active_dot} {label}</div>
                  <div class="key-card-vendor">{vendor_label}</div>
                </div>
                <div class="key-card-actions">
                  <button class="btn-icon" data-action="edit" data-key="{key_data}">\[edit]</button>
                  <button class="btn-icon danger" data-action="delete" data-key-id="{kid}" data-key-label="{label}">X</button>
                </div>
              </div>
              <div class="key-card-body">
                <div class="key-card-row"><span class="row-label">\u5957\u9910</span><span class="row-val">{plan_label}</span></div>
                <div class="key-card-row"><span class="row-label">Token</span><span class="row-val mono">***{last4}</span></div>
                <div class="key-card-row"><span class="row-label">\u4e0a\u6e38</span><span class="row-val mono small">{upstream}</span></div>
                <div class="key-card-row"><span class="row-label">Base URL</span><span class="row-val mono small copyable" data-url="{url_hint}">{url_hint}</span></div>
                <div class="key-card-row"><span class="row-label">\u521b\u5efa</span><span class="row-val">{created_str}</span></div>
                <div class="key-card-row"><span class="row-label">\u6700\u540e\u4f7f\u7528</span><span class="row-val">{last_used_str}</span></div>
              </div>
            </div>"""
    else:
        key_cards = """<div class="empty-state"><div class="empty-icon">Key</div>
          <div class="empty-title">\u8fd8\u6ca1\u6709 Key</div>
          <div class="empty-sub">\u70b9\u51fb\u53f3\u4e0a\u89d2\u300c+ \u6dfb\u52a0 Key\u300d\u5f00\u59cb</div></div>"""

    body = f"""
{topbar("settings")}
<div class="body">
  <div class="page-head">
    <div>
      <div class="page-title">Key \u7ba1\u7406</div>
      <div class="page-sub">{len(keys)} \u4e2a API Key \xb7 Token \u5b58\u7cfb\u7edf keychain</div>
    </div>
    <button class="btn-add" id="addBtn">+ \u6dfb\u52a0 Key</button>
  </div>

  <div class="notice">
    <strong>\u26a0 Token \u5b89\u5168</strong> \xb7 \u5b58\u7cfb\u7edf keychain\uff0c\u4e0d\u5199\u660e\u6587/\u4e0d\u8fdb\u65e5\u5fd7/\u4e0d\u4e0a\u4f20\u3002<strong>\u4e0d\u8981</strong>\u5728\u804a\u5929/\u622a\u56fe/issue \u8d34\u5b8c\u6574 token\u3002
  </div>

  <div class="key-grid">{key_cards}</div>
</div>

<!-- Modal -->
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title" id="modalTitle">\u6dfb\u52a0 Key</div>
      <button class="modal-close" id="modalClose">\u00d7</button>
    </div>
    <div class="modal-body">
      <input type="hidden" id="editKeyId" value="">
      <div class="field-row">
        <div class="field">
          <label class="field-label">\u540d\u79f0</label>
          <input id="m_label" type="text" class="field-input" placeholder="\u4f8b\uff1a\u667a\u8c31\u4e3b\u529b">
        </div>
        <div class="field">
          <label class="field-label">\u5382\u5546</label>
          <select id="m_vendor" class="field-input"></select>
        </div>
      </div>
      <div class="field">
        <label class="field-label">\u5957\u9910</label>
        <select id="m_plan" class="field-input"></select>
      </div>
      <div class="field">
        <label class="field-label">API Token <span class="hint">\u7f16\u8f91\u65f6\u7559\u7a7a=\u4e0d\u6539</span></label>
        <input id="m_token" type="password" class="field-input mono" placeholder="\u7c98\u8d34 token" autocomplete="off">
      </div>
      <div class="field">
        <label class="field-label">\u4e0a\u6e38 URL <span class="hint">\u9009\u5382\u5546\u81ea\u52a8\u586b</span></label>
        <input id="m_upstream" type="text" class="field-input mono">
      </div>
      <div class="field">
        <label class="field-label">Monitor API URL <span class="hint">\u7559\u7a7a=\u8be5\u5382\u5546\u4e0d\u652f\u6301</span></label>
        <input id="m_monitor" type="text" class="field-input mono">
      </div>
    </div>
    <div class="modal-foot">
      <button class="btn btn-ghost" id="modalCancel">\u53d6\u6d88</button>
      <button class="btn btn-primary" id="modalSave">\u4fdd\u5b58</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>
"""

    # JS is a plain string — no f-string, no Python brace conflicts
    js_block = """<script id="vendorsData" type="application/json">__VENDORS_JSON__</script>
<script>
(function() {
  var VENDORS = JSON.parse(document.getElementById('vendorsData').textContent);
  var overlay = document.getElementById('modalOverlay');
  var toastEl = document.getElementById('toast');
  var toastTimer;

  function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function() { toastEl.classList.remove('show'); }, 2500);
  }

  function populateVendorOptions() {
    var sel = document.getElementById('m_vendor');
    sel.innerHTML = '';
    Object.keys(VENDORS).forEach(function(k) {
      var o = document.createElement('option');
      o.value = k; o.textContent = VENDORS[k].label;
      sel.appendChild(o);
    });
  }
  function populatePlans(vendorKey, selected) {
    var v = VENDORS[vendorKey];
    var sel = document.getElementById('m_plan');
    sel.innerHTML = '';
    if (!v || !v.plans || v.plans.length === 0) {
      var o = document.createElement('option');
      o.value = 'custom'; o.textContent = '\u81ea\u5b9a\u4e49';
      sel.appendChild(o);
    } else {
      v.plans.forEach(function(p) {
        var o = document.createElement('option');
        o.value = p.id; o.textContent = p.label;
        if (p.id === selected) o.selected = true;
        sel.appendChild(o);
      });
    }
  }
  function updateDefaults(vendorKey) {
    var v = VENDORS[vendorKey];
    if (!v) return;
    document.getElementById('m_upstream').value = v.upstream_default || '';
    document.getElementById('m_monitor').value = v.monitor_url_default || '';
  }

  function openAddModal() {
    document.getElementById('modalTitle').textContent = '\u6dfb\u52a0 Key';
    document.getElementById('editKeyId').value = '';
    document.getElementById('m_label').value = '';
    document.getElementById('m_token').value = '';
    document.getElementById('m_token').placeholder = '\u7c98\u8d34 token\uff08\u5fc5\u586b\uff09';
    document.getElementById('m_upstream').value = '';
    document.getElementById('m_monitor').value = '';
    populateVendorOptions();
    populatePlans(document.getElementById('m_vendor').value, '');
    updateDefaults(document.getElementById('m_vendor').value);
    overlay.classList.add('show');
    setTimeout(function() { document.getElementById('m_label').focus(); }, 100);
  }

  function openEditModal(keyData) {
    document.getElementById('modalTitle').textContent = '\u7f16\u8f91 Key';
    document.getElementById('editKeyId').value = keyData.id;
    document.getElementById('m_label').value = keyData.label;
    document.getElementById('m_token').value = '';
    document.getElementById('m_token').placeholder = '\u7559\u7a7a=\u4e0d\u6539\u73b0\u6709 token';
    document.getElementById('m_upstream').value = keyData.upstream_url || '';
    document.getElementById('m_monitor').value = keyData.monitor_url || '';
    populateVendorOptions();
    var vsel = document.getElementById('m_vendor');
    for (var i = 0; i < vsel.options.length; i++) {
      if (vsel.options[i].value === keyData.vendor) { vsel.selectedIndex = i; break; }
    }
    populatePlans(keyData.vendor, keyData.plan);
    overlay.classList.add('show');
  }

  function closeModal() { overlay.classList.remove('show'); }

  document.getElementById('addBtn').addEventListener('click', openAddModal);
  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('modalCancel').addEventListener('click', closeModal);
  overlay.addEventListener('click', function(e) { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });

  document.getElementById('m_vendor').addEventListener('change', function(e) {
    populatePlans(e.target.value, '');
    updateDefaults(e.target.value);
  });

  document.getElementById('modalSave').addEventListener('click', function() {
    var kid = document.getElementById('editKeyId').value;
    var payload = {
      label: document.getElementById('m_label').value.trim(),
      vendor: document.getElementById('m_vendor').value,
      plan: document.getElementById('m_plan').value,
      upstream_url: document.getElementById('m_upstream').value,
      monitor_url: document.getElementById('m_monitor').value,
    };
    var token = document.getElementById('m_token').value;
    if (token) payload.token = token;
    if (!payload.label) { showToast('\u540d\u79f0\u5fc5\u586b'); return; }

    var url, method;
    if (kid) {
      url = '/__ledger__/api/keys/' + kid;
      method = 'PATCH';
    } else {
      if (!token) { showToast('\u65b0 Key \u5fc5\u987b\u586b token'); return; }
      url = '/__ledger__/api/keys';
      method = 'POST';
    }

    fetch(url, { method: method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.ok) {
          closeModal();
          showToast('\u2713 \u5df2\u4fdd\u5b58');
          setTimeout(function() { window.location.reload(); }, 600);
        } else {
          showToast('\u5931\u8d25: ' + (data.error || 'unknown'));
        }
      })
      .catch(function(err) { showToast('\u8bf7\u6c42\u5931\u8d25: ' + err); });
  });

  // Edit / delete buttons (event delegation)
  document.querySelector('.key-grid').addEventListener('click', function(e) {
    var btn = e.target.closest('[data-action]');
    if (!btn) return;
    if (btn.dataset.action === 'edit') {
      openEditModal(JSON.parse(btn.dataset.key));
    } else if (btn.dataset.action === 'delete') {
      var kid = btn.dataset.keyId;
      var label = btn.dataset.keyLabel;
      if (!confirm('\u786e\u8ba4\u5220\u9664\u300c' + label + '\u300d\uff1f')) return;
      fetch('/__ledger__/api/keys/' + kid, { method: 'DELETE' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.ok) { showToast('\u2713 \u5df2\u5220\u9664'); setTimeout(function() { window.location.reload(); }, 600); }
          else { showToast('\u5220\u9664\u5931\u8d25: ' + (data.error || '')); }
        });
    }
  });

  // Copyable base URLs
  document.querySelector('.key-grid').addEventListener('click', function(e) {
    var el = e.target.closest('.copyable');
    if (!el) return;
    navigator.clipboard.writeText(el.dataset.url).then(function() { showToast('\u2713 \u5df2\u590d\u5236'); });
  });
})();
</script>"""

    js_block = js_block.replace("__VENDORS_JSON__", vendors_json)
    full_body = body + "\n" + js_block
    return page_shell("Ledger \xb7 \u914d\u7f6e", full_body)
