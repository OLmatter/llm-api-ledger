"""
llm-api-ledger probe — main FastAPI app (multi-key).

Routes:
  /__ledger__                     — dashboard (all keys or one selected)
  /__ledger__/?key=<id>           — dashboard filtered to one key
  /__ledger__/settings            — key list + add/edit/delete
  /__ledger__/export              — export page (per-key)
  /__ledger__/api/keys            — GET list / POST create key
  /__ledger__/api/keys/<id>       — GET / PATCH / DELETE one key
  /__ledger__/api/keys/<id>/test-monitor — force poll one key
  /__ledger__/api/stats?key=<id>  — aggregate stats JSON
  /__ledger__/api/export?key=<id> — export bundle JSON
  /<vendor>/<path>                — transparent proxy (default key)
  /<vendor>/<label>/<path>        — transparent proxy (explicit key)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from probe import config_store, db, monitor, proxy, export
from probe.constants import DASHBOARD_WINDOW_DAYS, HOURLY_CHART_HOURS, DAILY_CHART_DAYS, RECENT_LIMIT
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


# ── Runtime state ─────────────────────────────────────────────────────────

_state: dict = {
    "monitor_stop": None,
    "monitor_task": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = _resolve_db_path()
    db.init_db(db_path)
    # Start monitor loop (multi-key)
    stop = asyncio.Event()
    _state["monitor_stop"] = stop
    _state["monitor_task"] = asyncio.create_task(
        monitor.poll_loop(_resolve_db_path, stop)
    )
    logger.info("probe ready — dashboard at /__ledger__")
    # Auto-open browser on first run if no keys configured
    keys = db.list_keys(db_path)
    if not keys:
        try:
            cfg = config_store.load_global_config()
            port = cfg.get("listen_port", 8080)
            webbrowser.open(f"http://127.0.0.1:{port}/__ledger__/settings")
        except Exception:
            pass
    yield
    stop.set()
    if _state["monitor_task"]:
        try:
            await asyncio.wait_for(_state["monitor_task"], timeout=5.0)
        except asyncio.TimeoutError:
            _state["monitor_task"].cancel()
    await proxy.aclose_client()


app = FastAPI(title="llm-api-ledger probe", lifespan=lifespan, redirect_slashes=False)


# ── Dashboard & UI routes ─────────────────────────────────────────────────


@app.get("/", include_in_schema=False)
async def index_redirect():
    return Response(status_code=302, headers={"Location": "/__ledger__/"})


@app.get("/__ledger", include_in_schema=False)
@app.get("/__ledger/", include_in_schema=False)
async def dashboard(key: int = Query(default=0)):
    return await _render_dashboard(key_id=key)


@app.get("/__ledger__/settings", include_in_schema=False)
async def settings_page():
    return await _render_settings()


@app.get("/__ledger__/export", include_in_schema=False)
async def export_page(key: int = Query(default=0)):
    return await _render_export_page(selected_key_id=key)


# ── API routes ─────────────────────────────────────────────────────────────


@app.get("/__ledger__/api/keys")
async def api_list_keys():
    db_path = _resolve_db_path()
    keys = db.list_keys(db_path)
    return {"keys": keys}


@app.post("/__ledger__/api/keys")
async def api_create_key(request: Request):
    db_path = _resolve_db_path()
    body = await request.json()
    label = (body.get("label") or "").strip()
    vendor = (body.get("vendor") or "").strip()
    plan = (body.get("plan") or "").strip()
    token = body.get("token") or ""
    upstream_url = body.get("upstream_url") or ""
    monitor_url = body.get("monitor_url") or ""
    monitor_interval_s = int(body.get("monitor_interval_s") or 300)
    notes = body.get("notes") or ""
    if not label:
        return JSONResponse({"ok": False, "error": "label required"}, status_code=400)
    if not vendor:
        return JSONResponse({"ok": False, "error": "vendor required"}, status_code=400)
    # Auto-fill upstream / monitor from vendor defaults if blank
    vinfo = config_store.VENDORS.get(vendor, {})
    if not upstream_url:
        upstream_url = vinfo.get("upstream_default", "")
    if not monitor_url:
        monitor_url = vinfo.get("monitor_url_default", "")
    new = config_store.add_key(
        db_path, label=label, vendor=vendor, plan=plan,
        upstream_url=upstream_url, monitor_url=monitor_url, token=token,
        monitor_interval_s=monitor_interval_s, notes=notes,
        salt=config_store.get_salt(),
    )
    if not new:
        return JSONResponse({"ok": False, "error": "label already exists"}, status_code=409)
    return {"ok": True, "key": new}


@app.get("/__ledger__/api/keys/{key_id}")
async def api_get_key(key_id: int):
    db_path = _resolve_db_path()
    k = db.get_key(db_path, key_id)
    if not k:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True, "key": k}


@app.patch("/__ledger__/api/keys/{key_id}")
async def api_patch_key(key_id: int, request: Request):
    db_path = _resolve_db_path()
    body = await request.json()
    new_token = body.pop("token", None)
    updates = {k: v for k, v in body.items() if v is not None}
    # Auto-fill upstream/monitor from vendor defaults if vendor changed
    if "vendor" in updates:
        vinfo = config_store.VENDORS.get(updates["vendor"], {})
        if "upstream_url" not in updates:
            updates["upstream_url"] = vinfo.get("upstream_default", "")
        if "monitor_url" not in updates:
            updates["monitor_url"] = vinfo.get("monitor_url_default", "")
    k = config_store.update_key(db_path, key_id, updates, new_token=new_token,
                                salt=config_store.get_salt())
    if not k:
        return JSONResponse({"ok": False, "error": "not found or update failed"}, status_code=404)
    return {"ok": True, "key": k}


@app.delete("/__ledger__/api/keys/{key_id}")
async def api_delete_key(key_id: int):
    db_path = _resolve_db_path()
    ok = config_store.remove_key(db_path, key_id)
    if not ok:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True}


@app.get("/__ledger__/api/keys/{key_id}/test-monitor")
async def api_test_key_monitor(key_id: int):
    """Force a one-off monitor poll for one key. Returns the parsed periods."""
    db_path = _resolve_db_path()
    k = db.get_key(db_path, key_id)
    if not k:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    salt = config_store.get_salt()
    periods = await monitor.poll_key(db_path, k, salt)
    return {"ok": True, "periods": periods, "label": k.get("label", "")}


@app.get("/__ledger__/api/stats")
async def api_stats(key: int = Query(default=0), days: int = Query(default=30, ge=1, le=365)):
    db_path = _resolve_db_path()
    stats = db.aggregate_stats(db_path, key_id=key, days=days)
    keys = db.list_keys(db_path)
    stats["keys"] = keys
    stats["selected_key_id"] = key
    return stats


@app.get("/__ledger__/api/export")
async def api_export(key: int = Query(default=0), days: int = Query(default=7, ge=1, le=90)):
    db_path = _resolve_db_path()
    bundle = export.build_export_bundle(db_path, days=days, key_id=key)
    md = export.render_pr_description(bundle)
    fname = export.bundle_filename(bundle)
    return {"ok": True, "filename": fname, "bundle": bundle, "pr_description": md}


# ── Transparent proxy (catch-all) ─────────────────────────────────────────

_SILENT_PATHS = {"favicon.ico", "robots.txt"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def transparent_proxy(path: str, request: Request):
    if request.method in ("GET", "HEAD") and path in _SILENT_PATHS:
        return Response(status_code=204)
    # Never forward our internal __ledger__ namespace upstream
    if path in ("__ledger__", "__ledger__/"):
        key_param = request.query_params.get("key", "0")
        return await _render_dashboard(key_id=int(key_param))
    if path == "__ledger__/settings":
        return await _render_settings()
    if path == "__ledger__/export":
        export_key = request.query_params.get("key", "0")
        return await _render_export_page(selected_key_id=int(export_key))
    if path.startswith("__ledger__"):
        return Response(status_code=302, headers={"Location": "/__ledger__/"})

    method = request.method
    headers = dict(request.headers.items())
    body = await request.body()
    db_path = _resolve_db_path()
    try:
        status, out_headers, body_out, err = await proxy.proxy_request(
            method, path, headers, body, db_path,
        )
    except Exception as e:
        logger.exception("proxy crash")
        return JSONResponse(
            {"error": {"type": "proxy_crash", "message": str(e)[:200]}},
            status_code=502,
        )
    if status == 0:
        # Proxy couldn't dispatch (no key configured, etc.)
        return JSONResponse(
            {"error": {"type": "no_key", "message": err or "no key configured"}},
            status_code=400,
        )
    if asyncio.iscoroutinefunction(body_out) or hasattr(body_out, "__aiter__") or hasattr(body_out, "__anext__"):
        return StreamingResponse(
            body_out,
            media_type=out_headers.get("content-type", "text/event-stream"),
            headers=out_headers,
        )
    return Response(content=body_out, status_code=status, headers=out_headers)


# ── Render helpers ────────────────────────────────────────────────────────


async def _render_dashboard(key_id: int = 0) -> HTMLResponse:
    db_path = _resolve_db_path()
    stats = db.aggregate_stats(db_path, key_id=key_id, days=DASHBOARD_WINDOW_DAYS)
    hourly = db.hourly_series(db_path, hours=HOURLY_CHART_HOURS, key_id=key_id)
    daily = db.daily_series(db_path, days=DAILY_CHART_DAYS, key_id=key_id)
    keys = db.list_keys(db_path)
    selected_key = db.get_key(db_path, key_id) if key_id else None
    cfg = config_store.load_global_config()
    return HTMLResponse(dash_tpl.render(stats, cfg, hourly, daily, keys, selected_key))


async def _render_settings() -> HTMLResponse:
    db_path = _resolve_db_path()
    keys = db.list_keys(db_path)
    cfg = config_store.load_global_config()
    return HTMLResponse(settings_tpl.render(keys, cfg))


async def _render_export_page(selected_key_id: int = 0) -> HTMLResponse:
    db_path = _resolve_db_path()
    keys = db.list_keys(db_path)
    selected_key = db.get_key(db_path, selected_key_id) if selected_key_id else None
    return HTMLResponse(export_tpl.render(keys, selected_key))


# ── Entry point ───────────────────────────────────────────────────────────


def main():
    import uvicorn

    cfg = config_store.load_global_config()
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
