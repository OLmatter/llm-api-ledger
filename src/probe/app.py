"""
llm-api-ledger probe — main FastAPI app.

Single entry point. Run with:
    uvicorn probe.app:app --host 127.0.0.1 --port 8080

Routes:
  /__ledger__            — dashboard (HTML)
  /__ledger__/settings   — config page (HTML)
  /__ledger__/export     — export page (HTML)
  /__ledger__/api/stats  — aggregate stats (JSON)
  /__ledger__/api/settings — POST/GET config (JSON)
  /__ledger__/api/token    — DELETE clears token
  /__ledger__/api/export   — GET export bundle (JSON)
  /<vendor>/<path>       — transparent proxy (any method)
  /<path>                — transparent proxy (uses configured vendor)

The /__ledger__/* paths are prefixed with __ledger__ to keep them distinct
from real upstream paths (e.g. /v1/messages from Anthropic).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

# Make `probe.*` imports work both when run as a module (-m probe.app) and as a script
HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from probe import config_store, db, monitor, proxy, export
from probe.templates import dashboard as dash_tpl
from probe.templates import settings as settings_tpl
from probe.templates import export_page as export_tpl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ledger")


def _resolve_db_path() -> Path:
    return db.get_db_path()


# ── Runtime state (single process; FastAPI runs on one event loop) ────────

_state: dict = {
    "cfg_cache": None,        # cached config dict
    "cfg_lock": threading.Lock(),
    "monitor_stop": None,     # asyncio.Event set on shutdown
    "monitor_task": None,
}


def _cfg_getter():
    """Return the current config dict (re-read on demand). The monitor loop
    and the proxy both call this so config changes take effect without restart."""
    with _state["cfg_lock"]:
        if _state["cfg_cache"] is None:
            _state["cfg_cache"] = config_store.load_config()
        return _state["cfg_cache"]


def _refresh_cfg() -> dict:
    with _state["cfg_lock"]:
        _state["cfg_cache"] = config_store.load_config()
        return _state["cfg_cache"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = _resolve_db_path()
    db.init_db(db_path)
    # Refresh config + ensure user_hash is set if token exists
    cfg = _refresh_cfg()
    token = config_store.get_token()
    if token and not cfg.get("user_hash"):
        config_store.recompute_user_hash(cfg)
        _refresh_cfg()
    # Start monitor loop
    stop = asyncio.Event()
    _state["monitor_stop"] = stop
    _state["monitor_task"] = asyncio.create_task(
        monitor.poll_loop(_cfg_getter, db_path, stop)
    )
    logger.info("probe ready — dashboard at /__ledger__")
    # Auto-open browser on first run (only if config is incomplete)
    if not config_store.has_token():
        try:
            port = cfg.get("listen_port", 8080)
            webbrowser.open(f"http://127.0.0.1:{port}/__ledger__/settings")
        except Exception:
            pass
    yield
    # Shutdown
    stop.set()
    if _state["monitor_task"]:
        try:
            await asyncio.wait_for(_state["monitor_task"], timeout=5.0)
        except asyncio.TimeoutError:
            _state["monitor_task"].cancel()
    await proxy.aclose_client()


app = FastAPI(title="llm-api-ledger probe", lifespan=lifespan)


# ── Dashboard & UI routes ──────────────────────────────────────────────────


@app.get("/", include_in_schema=False)
async def index_redirect():
    return Response(status_code=302, headers={"Location": "/__ledger__"})


@app.get("/__ledger", include_in_schema=False)
@app.get("/__ledger/", include_in_schema=False)
async def dashboard():
    db_path = _resolve_db_path()
    stats = db.aggregate_stats(db_path, days=30)
    cfg = _cfg_getter()
    cfg_view = dict(cfg)
    cfg_view["has_token"] = config_store.has_token()
    html_content = dash_tpl.render(stats, cfg_view)
    return HTMLResponse(html_content)


@app.get("/__ledger__/settings", include_in_schema=False)
async def settings_page():
    cfg = _cfg_getter()
    return HTMLResponse(settings_tpl.render(cfg, config_store.has_token()))


@app.get("/__ledger__/export", include_in_schema=False)
async def export_page():
    cfg = _cfg_getter()
    return HTMLResponse(export_tpl.render(cfg))


# ── API routes ─────────────────────────────────────────────────────────────


@app.get("/__ledger__/api/stats")
async def api_stats(days: int = Query(default=30, ge=1, le=365)):
    db_path = _resolve_db_path()
    stats = db.aggregate_stats(db_path, days=days)
    cfg = _cfg_getter()
    stats["vendor"] = cfg.get("vendor", "")
    stats["plan"] = cfg.get("plan", "")
    stats["has_token"] = config_store.has_token()
    stats["user_hash"] = cfg.get("user_hash", "")
    return stats


@app.get("/__ledger__/api/settings")
async def api_get_settings():
    cfg = _cfg_getter()
    view = {k: v for k, v in cfg.items() if k not in {"salt"}}
    view["has_token"] = config_store.has_token()
    return view


@app.post("/__ledger__/api/settings")
async def api_post_settings(request: Request):
    body = await request.json()
    cfg = _cfg_getter()
    # Apply non-secret updates
    for k in ("vendor", "plan", "upstream_url", "monitor_url",
              "listen_port", "monitor_interval_s", "opt_in_upload",
              "relay_plan_label"):
        if k in body:
            cfg[k] = body[k]
    # Token: if supplied, store in keychain (never in config.json)
    if body.get("token"):
        ok = config_store.set_token(body["token"])
        if not ok:
            return JSONResponse({"ok": False, "error": "keychain_set_failed"}, status_code=500)
    config_store.recompute_user_hash(cfg)
    config_store.save_config(cfg)
    _refresh_cfg()
    return {"ok": True, "has_token": config_store.has_token()}


@app.delete("/__ledger__/api/token")
async def api_delete_token():
    try:
        import keyring  # type: ignore

        keyring.delete_password(config_store._KEYRING_SERVICE, config_store._KEYRING_USER)
    except Exception as e:
        # Not an error if the password didn't exist
        logger.info("keyring delete: %s", e)
    cfg = _cfg_getter()
    cfg["user_hash"] = ""
    config_store.save_config(cfg)
    _refresh_cfg()
    return {"ok": True}


@app.get("/__ledger__/api/export")
async def api_export(days: int = Query(default=7, ge=1, le=90)):
    db_path = _resolve_db_path()
    bundle = export.build_export_bundle(db_path, days=days)
    md = export.render_pr_description(bundle)
    fname = export.bundle_filename(bundle)
    return {"ok": True, "filename": fname, "bundle": bundle, "pr_description": md}


@app.get("/__ledger__/api/test-monitor")
async def api_test_monitor():
    """Force a one-off monitor poll for debugging. Returns the parsed periods."""
    cfg = _cfg_getter()
    db_path = _resolve_db_path()
    periods = await monitor.poll_once(cfg, db_path)
    return {"ok": True, "periods": periods, "vendor": cfg.get("vendor", "")}


# ── Transparent proxy (catch-all) ─────────────────────────────────────────
# IMPORTANT: this must be the LAST route registered. Any path that didn't
# match a /__ledger__/* route is forwarded upstream verbatim.

# Reserve a few well-known paths to silently 204 (like api-meter does for probes)
_SILENT_PATHS = {"favicon.ico", "robots.txt"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def transparent_proxy(path: str, request: Request):
    if request.method in ("GET", "HEAD") and path in _SILENT_PATHS:
        return Response(status_code=204)
    # Safety net: if a request slips past the explicit /__ledger__ routes
    # (e.g. trailing-slash variants), don't forward it upstream — it would
    # leak our internal path namespace to the vendor.
    if path == "__ledger__" or path.startswith("__ledger__/"):
        return Response(status_code=302, headers={"Location": "/__ledger__/"})
    method = request.method
    headers = dict(request.headers.items())
    body = await request.body()
    db_path = _resolve_db_path()
    try:
        status, out_headers, body_out = await proxy.proxy_request(
            method, path, headers, body, _cfg_getter, db_path,
        )
    except Exception as e:
        logger.exception("proxy crash")
        return JSONResponse(
            {"error": {"type": "proxy_crash", "message": str(e)[:200]}},
            status_code=502,
        )
    if asyncio.iscoroutinefunction(body_out) or hasattr(body_out, "__aiter__") or hasattr(body_out, "__anext__"):
        # streaming generator
        return StreamingResponse(body_out, media_type=out_headers.get("content-type", "text/event-stream"), headers=out_headers)
    return Response(content=body_out, status_code=status, headers=out_headers)


# ── Entry point for `python -m probe.app` or direct script run ────────────


def main():
    import uvicorn

    cfg = config_store.load_config()
    port = int(os.environ.get("LEDGER_PORT", cfg.get("listen_port", 8080)))
    host = os.environ.get("LEDGER_HOST", "127.0.0.1")
    logger.info("starting probe on %s:%d", host, port)
    uvicorn.run(
        "probe.app:app",
        host=host,
        port=port,
        log_level=os.environ.get("LEDGER_LOG_LEVEL", "info"),
        reload=False,
    )


if __name__ == "__main__":
    main()
