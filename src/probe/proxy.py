"""
Transparent proxy (multi-key).

URL formats:
  /<vendor_prefix>/<path>                       → uses the vendor's default
                                                   active key (first one in DB)
  /<vendor_prefix>/<key_label>/<path>           → uses the named key explicitly

The proxy:
  1. Resolves (vendor, key_label) → key_id + upstream URL + token
  2. Forwards the IDE request upstream with the key's token
  3. Streams the response back unchanged
  4. Records metrics (ttft, tps, status, timeout_type, error_type, stop_signal)
     tagged with key_id

Timeout taxonomy (see elm_7d3aec1bf664):
  - connect_timeout / read_timeout / ttft_timeout / stream_stall_timeout
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any

import httpx

from . import config_store
from . import db
from .constants import (
    CONNECT_TIMEOUT_S, READ_TIMEOUT_S, TTFT_TIMEOUT_S, STALL_TIMEOUT_S,
    MAX_CONNECTIONS, MAX_KEEPALIVE_CONNECTIONS,
)

logger = logging.getLogger("ledger.proxy")

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


def filter_upstream_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}


def resolve_route(db_path, path: str) -> tuple[dict[str, Any] | None, str, str]:
    """Parse `path` (after leading /) into (key_row, rest_path, error_msg).

    URL forms:
      zhipu/v1/messages                  → vendor=zhipu, key=vendor's default
      zhipu/主力号/v1/messages           → vendor=zhipu, key=label '主力号'
      zhipu/main/v1/messages             → ambiguous: 'main' could be label or path
                                           we check if a key with that label exists;
                                           if yes treat as key, else treat as path

    Returns:
      (key_row, rest, "") on success
      (None, "", error_msg) on failure
    """
    parts = path.split("/", 1)
    if not parts or not parts[0]:
        return (None, "", "empty path")
    vendor_prefix = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    vendor_key = config_store.vendor_key_by_prefix(vendor_prefix)
    if not vendor_key:
        return (None, "", f"unknown vendor prefix: {vendor_prefix}")

    # Try to extract key_label from the next path segment
    if "/" in rest:
        head, tail = rest.split("/", 1)
        candidate = db.get_key_by_label(db_path, head) if head else None
        if candidate and candidate.get("vendor") == vendor_key:
            return (candidate, tail, "")
    # No key_label in URL, or no such label: fall back to vendor's first active key
    keys = db.list_keys(db_path)
    active_for_vendor = [k for k in keys if k.get("is_active") and k.get("vendor") == vendor_key]
    if not active_for_vendor:
        # Also try inactive (so the user can still see why it's failing)
        any_for_vendor = [k for k in keys if k.get("vendor") == vendor_key]
        if any_for_vendor:
            return (None, rest, f"no active key for vendor '{vendor_prefix}' (key disabled?)")
        return (None, rest, f"no key configured for vendor '{vendor_prefix}'. Add one in /__ledger__/settings")
    return (active_for_vendor[0], rest, "")


def build_upstream_url(key_row: dict[str, Any], rest: str) -> str:
    base = (key_row.get("upstream_url") or "").rstrip("/")
    if not rest:
        return base
    return f"{base}/{rest}"


# ── Token / usage extraction ──────────────────────────────────────────────


def normalize_usage(usage: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(usage, dict):
        return {"in": 0, "out": 0, "cc": 0, "cr": 0}
    return {
        "in": int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
        "out": int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
        "cc": int(usage.get("cache_creation_input_tokens") or usage.get("cache_creation") or 0),
        "cr": int(usage.get("cache_read_input_tokens") or usage.get("cache_read") or usage.get("cached_tokens") or 0),
    }


def extract_effort(body_json: dict[str, Any]) -> str:
    thinking = body_json.get("thinking") or {}
    if isinstance(thinking, dict):
        et = thinking.get("effort") or thinking.get("type")
        if et:
            return str(et)
    if body_json.get("reasoning_effort"):
        return str(body_json.get("reasoning_effort"))
    return ""


def classify_error(status_code: int, body_text: str) -> tuple[str, str]:
    try:
        data = json.loads(body_text)
        if isinstance(data, dict):
            err = data.get("error") or data
            if isinstance(err, dict):
                etype = str(err.get("type") or err.get("code") or "")
                emsg = str(err.get("message") or err.get("detail") or "")
            else:
                etype, emsg = "", str(err)
        else:
            etype, emsg = "", str(data)
    except Exception:
        etype, emsg = "", body_text[:200]
    if not etype:
        if status_code == 402:
            etype = "insufficient_quota"
        elif status_code == 429:
            etype = "rate_limited"
        elif status_code == 529:
            etype = "overloaded"
        elif 500 <= status_code < 600:
            etype = "server_error"
        elif 400 <= status_code < 500:
            etype = "client_error"
    h = hashlib.sha256(emsg.encode("utf-8")).hexdigest()[:16] if emsg else ""
    return etype, h


def classify_stop_signal(status_code: int, timeout_type: str, did_complete: bool) -> str:
    if timeout_type:
        return timeout_type
    if status_code == 402:
        return "payment_required_402"
    if status_code == 429:
        return "rate_limited_429"
    if status_code == 529:
        return "overloaded_529"
    if 500 <= status_code < 600:
        return "server_error_5xx"
    if status_code >= 400:
        return "client_error_4xx"
    if not did_complete:
        return "silent_failure"
    return ""


# ── HTTP client ────────────────────────────────────────────────────────────

_shared_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            http2=False,
            limits=httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS),
        )
    return _shared_client


async def aclose_client() -> None:
    global _shared_client
    if _shared_client is not None and not _shared_client.is_closed:
        await _shared_client.aclose()
    _shared_client = None


# ── Proxy entry ────────────────────────────────────────────────────────────


async def proxy_request(
    method: str,
    path: str,
    request_headers: dict[str, str],
    body: bytes,
    db_path,
) -> tuple[int, dict[str, str], Any, str]:
    """Proxy one request.

    Returns (status, headers, body-or-generator, error_msg).
    status=0 with non-empty error_msg means the proxy couldn't dispatch
    (e.g. no key configured); the caller should turn that into a 4xx.
    """
    start = time.time()

    # Parse body for model / stream / effort
    model = ""
    num_messages = 0
    is_stream = False
    effort = ""
    if body:
        try:
            bj = json.loads(body)
            if isinstance(bj, dict):
                model = str(bj.get("model") or "")
                is_stream = bool(bj.get("stream"))
                msgs = bj.get("messages") or []
                if isinstance(msgs, list):
                    num_messages = len(msgs)
                effort = extract_effort(bj)
        except Exception:
            pass

    # Resolve key + upstream
    key_row, rest, err = resolve_route(db_path, path)
    if not key_row:
        return (0, {}, None, err or "no key configured for this path")

    upstream_url = build_upstream_url(key_row, rest)
    if not upstream_url:
        return (0, {}, None, f"key '{key_row['label']}' has no upstream_url set")

    key_id = key_row["id"]
    vendor = key_row.get("vendor", "")
    plan = key_row.get("plan", "")
    salt = config_store.get_salt()
    user_hash = config_store.compute_user_hash(
        config_store.get_token_for_key(key_row["label"]) or "", salt)

    # Rewrite Authorization header with this key's token (override whatever
    # the IDE sent — IDE may have a stale token, our keychain is authoritative)
    token = config_store.get_token_for_key(key_row["label"]) or ""
    vinfo = config_store.VENDORS.get(vendor, {})
    auth_value = f"Bearer {token}" if vinfo.get("auth_scheme") == "Bearer" else token
    auth_header_name = vinfo.get("auth_header", "Authorization")
    headers = filter_upstream_headers(request_headers)
    if token:
        headers[auth_header_name] = auth_value
    # Update last_used_at in background (best-effort)
    try:
        db.touch_key_last_used(db_path, key_id)
    except Exception as _e:
        logger.warning("touch_key_last_used failed: %s", _e)

    client = get_client()

    if is_stream:
        return await _proxy_stream(
            client, method, upstream_url, headers, body,
            start, key_id, vendor, plan, model, rest,
            num_messages, effort, user_hash, db_path,
        )

    # ── Non-streaming ──────────────────────────────────────────────────
    timeout_type = ""
    try:
        resp = await asyncio.wait_for(
            client.request(method, upstream_url, headers=headers, content=body),
            timeout=READ_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        timeout_type = "read_timeout"
        _record(
            db_path, start, key_id, vendor, plan, model, rest,
            usage={}, status_code=0, ttft_ms=0, tps_mean=0.0,
            error_type="timeout", error_msg_hash="",
            timeout_type=timeout_type, stop_signal="read_timeout",
            did_complete=False, num_messages=num_messages, effort=effort, user_hash=user_hash,
        )
        return (504, {"content-type": "application/json"}, b'{"error":{"type":"read_timeout"}}', "")
    except httpx.ConnectError:
        timeout_type = "connect_timeout"
        _record(
            db_path, start, key_id, vendor, plan, model, rest,
            usage={}, status_code=0, ttft_ms=0, tps_mean=0.0,
            error_type="connect_failed", error_msg_hash="",
            timeout_type=timeout_type, stop_signal="connect_timeout",
            did_complete=False, num_messages=num_messages, effort=effort, user_hash=user_hash,
        )
        return (502, {"content-type": "application/json"}, b'{"error":{"type":"connect_failed"}}', "")
    except Exception as e:
        logger.exception("proxy non-stream error")
        _record(
            db_path, start, key_id, vendor, plan, model, rest,
            usage={}, status_code=0, ttft_ms=0, tps_mean=0.0,
            error_type="proxy_error", error_msg_hash=hashlib.sha256(str(e).encode()).hexdigest()[:16],
            timeout_type="", stop_signal="proxy_error",
            did_complete=False, num_messages=num_messages, effort=effort, user_hash=user_hash,
        )
        return (502, {"content-type": "application/json"}, b'{"error":{"type":"proxy_error"}}', "")

    latency_ms = int((time.time() - start) * 1000)
    usage = normalize_usage({})
    try:
        usage = normalize_usage(resp.json().get("usage", {}))
    except Exception as _e:
        logger.warning("usage parse failed: %s", _e)
    body_bytes = resp.content
    err_type, err_hash = "", ""
    if resp.status_code >= 400:
        try:
            err_type, err_hash = classify_error(resp.status_code, resp.text)
        except Exception:
            pass
    stop_signal = classify_stop_signal(resp.status_code, "", did_complete=True)
    ttft_ms = latency_ms
    tps = (usage["out"] / (latency_ms / 1000.0)) if (usage["out"] and latency_ms > 0) else 0.0
    _record(
        db_path, start, key_id, vendor, plan, model, rest,
        usage=usage, status_code=resp.status_code, ttft_ms=ttft_ms, tps_mean=tps,
        error_type=err_type, error_msg_hash=err_hash,
        timeout_type="", stop_signal=stop_signal,
        did_complete=True, num_messages=num_messages, effort=effort, user_hash=user_hash,
    )
    out_headers = {"content-type": resp.headers.get("content-type", "application/json")}
    return (resp.status_code, out_headers, body_bytes, "")


async def _proxy_stream(
    client: httpx.AsyncClient, method: str, url: str, headers: dict[str, str], body: bytes,
    start: float, key_id: int, vendor: str, plan: str, model: str, endpoint: str,
    num_messages: int, effort: str, user_hash: str, db_path,
) -> tuple[int, dict[str, str], Any, str]:
    state = {
        "ttft_ms": 0,
        "last_line_ts": start,
        "timeout_type": "",
        "usage": {"in": 0, "out": 0, "cc": 0, "cr": 0},
        "status_code": 0,
        "error_type": "",
        "error_msg_hash": "",
        "did_complete": True,
    }

    def merge_usage(delta: dict[str, Any]) -> None:
        norm = normalize_usage(delta)
        for k in state["usage"]:
            if norm[k] > 0:
                state["usage"][k] = norm[k]

    async def generator():
        try:
            req = client.build_request(method, url, headers=headers, content=body)
            resp = await client.send(req, stream=True)
            state["status_code"] = resp.status_code
            if resp.status_code >= 400:
                body_bytes = await resp.aread()
                try:
                    state["error_type"], state["error_msg_hash"] = classify_error(
                        resp.status_code, body_bytes.decode("utf-8", "replace"))
                except Exception:
                    pass
                state["did_complete"] = False
                yield body_bytes
                await resp.aclose()
                return
            first_seen = False
            async for raw_line in resp.aiter_lines():
                now = time.time()
                if not first_seen and raw_line.strip():
                    state["ttft_ms"] = int((now - start) * 1000)
                    first_seen = True
                    state["last_line_ts"] = now
                else:
                    gap = now - state["last_line_ts"]
                    if gap > STALL_TIMEOUT_S and first_seen:
                        state["timeout_type"] = "stream_stall_timeout"
                    state["last_line_ts"] = now
                yield raw_line + "\n"
                if raw_line.startswith("data: "):
                    try:
                        data = json.loads(raw_line[6:])
                        t = data.get("type", "")
                        if t == "message_start":
                            mu = data.get("message", {}).get("usage", {})
                            if isinstance(mu, dict):
                                merge_usage(mu)
                        elif t == "message_delta":
                            du = data.get("usage", {})
                            if isinstance(du, dict):
                                merge_usage(du)
                        elif data.get("object") == "chat.completion.chunk":
                            cu = data.get("usage")
                            if isinstance(cu, dict):
                                merge_usage(cu)
                    except Exception:
                        pass
            await resp.aclose()
        except httpx.ConnectError:
            state["timeout_type"] = "connect_timeout"
            state["did_complete"] = False
            state["error_type"] = "connect_failed"
            yield b'data: {"type":"error","error":{"type":"connect_failed"}}\n\n'
        except Exception as e:
            state["timeout_type"] = state["timeout_type"] or "read_timeout"
            state["did_complete"] = False
            state["error_type"] = state["error_type"] or "timeout"
            logger.warning("stream error: %s", e)
            yield b'data: {"type":"error","error":{"type":"timeout"}}\n\n'
        finally:
            latency_ms = int((time.time() - start) * 1000)
            usage = state["usage"]
            tps = (usage["out"] / (latency_ms / 1000.0)) if (usage["out"] and latency_ms > 0) else 0.0
            stop_signal = classify_stop_signal(
                state["status_code"], state["timeout_type"], state["did_complete"])
            _record(
                db_path, start, key_id, vendor, plan, model, endpoint,
                usage=usage, status_code=state["status_code"],
                ttft_ms=state["ttft_ms"], tps_mean=tps,
                error_type=state["error_type"], error_msg_hash=state["error_msg_hash"],
                timeout_type=state["timeout_type"], stop_signal=stop_signal,
                did_complete=state["did_complete"],
                num_messages=num_messages, effort=effort, user_hash=user_hash,
            )

    return (200, {"content-type": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"}, generator(), "")


# ── Recording helper ──────────────────────────────────────────────────────


def _record(
    db_path, start_ts: float, key_id: int, vendor: str, plan: str, model: str, endpoint: str,
    usage: dict[str, int], status_code: int, ttft_ms: int, tps_mean: float,
    error_type: str, error_msg_hash: str, timeout_type: str, stop_signal: str,
    did_complete: bool, num_messages: int, effort: str, user_hash: str,
) -> None:
    latency_ms = int((time.time() - start_ts) * 1000)
    rec = {
        "ts": start_ts,
        "ts_text": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key_id": key_id,
        "vendor": vendor,
        "plan": plan,
        "model": model,
        "endpoint": endpoint,
        "input_tokens": usage.get("in", 0),
        "output_tokens": usage.get("out", 0),
        "cache_creation_tokens": usage.get("cc", 0),
        "cache_read_tokens": usage.get("cr", 0),
        "ttft_ms": ttft_ms,
        "total_latency_ms": latency_ms,
        "tps_mean": tps_mean,
        "status_code": status_code,
        "error_type": error_type,
        "error_message_hash": error_msg_hash,
        "timeout_type": timeout_type,
        "stop_signal": stop_signal,
        "user_hash": user_hash,
        "request_did_complete": did_complete,
        "num_messages": num_messages,
        "effort": effort,
    }
    db.save_request(db_path, rec)
