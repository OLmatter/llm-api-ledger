"""
Shared template helpers.

CSS is loaded from static/base.css ONCE and injected into every page.
No triple-quoted CSS blocks in any template — kills the escape-chain trap.
"""

from __future__ import annotations

from pathlib import Path

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

_css_cache: str | None = None


def load_base_css() -> str:
    """Load and cache static/base.css. Cached so we don't hit disk per request."""
    global _css_cache
    if _css_cache is None:
        css_path = _STATIC_DIR / "base.css"
        _css_cache = css_path.read_text(encoding="utf-8")
    return _css_cache


def page_shell(title: str, body: str, extra_head: str = "") -> str:
    """Wrap body content in a standard HTML page with base.css injected."""
    css = load_base_css()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
{extra_head}
</head>
<body>
{body}
</body>
</html>"""


def topbar(active: str = "") -> str:
    """Shared navigation bar. active = 'dashboard' | 'settings' | 'export'."""
    items = [
        ("dashboard", "账单", "/__ledger__/"),
        ("settings", "配置", "/__ledger__/settings"),
        ("export", "导出", "/__ledger__/export"),
    ]
    nav_html = ""
    for key, label, href in items:
        cls = "active" if key == active else ""
        nav_html += f'<a href="{href}" class="{cls}">{label}</a>'
    return f"""
<div class="topbar">
  <div class="topbar-brand">
    <div class="brand-logo">L</div>
    <div>
      <div class="brand-name">Ledger</div>
      <div class="brand-sub">本地核账</div>
    </div>
  </div>
  <nav class="nav">{nav_html}</nav>
</div>"""
