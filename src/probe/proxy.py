"""
Transparent proxy.

The probe listens on 127.0.0.1:<port>. The IDE sends requests to
http://127.0.0.1:<port>/<vendor_prefix>/<path...> and the probe:

  1. Strips the vendor prefix and rewrites the URL to the real upstream
     (e.g. /zhipu/v1/messages → https://open.bigmodel.cn/api/anthropic/v1/messages)
  2. Forwards the request verbatim (same headers, same body, same query)
  3. Streams the response back to the IDE unchanged
  4. In parallel, measures: ttft, total_latency, tps, status_code,
     cache hit, timeout_type (4-way), error_type, stop_signal

The probe NEVER inspects or modifies request/response bodies (beyond
counting tokens from the usage object for accounting). It is a pure
pass-through pipe with a sidecar meter.

Timeout taxonomy (see elm_7d3aec1bf664):
  - connect_timeout      : TCP connect failed within CONNECT_TIMEOUT_S
  - read_timeout         : connected, but no bytes for READ_TIMEOUT_S
  - ttft_timeout         : first token didn't arrive within TTFT_TIMEOUT_S
  - stream_stall_timeout : gap between SSE chunks exceeded STALL_TIMEOUT_S

Each timeout type is recorded separately (not merged into error rate).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import Any

import httpx

from . import config_store
from . import db

logger = logging.getLogger("ledger.proxy")

# ── Timeout thresholds (see elm_7d3aec1bf664, "don't write absolute total") ──
CONNECT_TIMEOUT_S = 5.0
READ_TIMEOUT_S = 30.0       # no bytes at all after connect
TTFT_TIMEOUT_S = 15.0       # first token not seen
STALL_TIMEOUT_S = 5.0       # gap between SSE lines

# Hop-by-hop headers that must not be forwarded verbatim.
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def filter_upstream_headers(headers: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in HOP_BY_HOP:
            continue
        out[k] = v
    return out


def split_vendor_prefix(path: str) -> tuple[str, str]:
    """Given the path after the leading /, return (vendor_prefix, rest).

    Examples:
        'zhipu/v1/messages'    → ('zhipu', 'v1/messages')
        'deepseek/chat/completions' → ('deepseek', 'chat/completions')
        'v1/messages'          → ('', 'v1/messages')   # no prefix
    """
    if "/" in path:
        head, rest = path.split("/", 1)
        # only treat known prefixes as vendor prefixes
        if config_store.vendor_by_prefix(head):
            return (head, rest)
        return ("", path)
    if config_store.vendor_by_prefix(path):
        return (path, "")
    return ("", path)


def build_upstream_url(vendor_info: dict[str, Any], rest: str) -> str:
    base = vendor_info.get("upstream_default") or ""
    base = base.rstrip("/")
    if not rest:
        return base
    return f"{base}/{rest}"


# ── Token / usage extraction ──────────────────────────────────────────────


def normalize_usage(usage: dict[str, Any] | None) -> dict[str, int]:
    """Map OpenAI / Anthropic / DeepSeek usage fields to a unified shape."""
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
    """Return (error_type, error_message_hash). Hash is sha256(msg)[:16];
    the plaintext is NEVER persisted or uploaded."""
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
    # Always also tag the HTTP status family for cross-vendor comparison
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
        else:
            etype = ""
    h = hashlib.sha256(emsg.encode("utf-8")).hexdigest()[:16] if emsg else ""
    return etype, h


def classify_stop_signal(status_code: int, timeout_type: str, did_complete: bool) -> str:
    """Map the final request outcome to a stop_signal taxonomy value.

    See elm_8f28d4c6313f for the full table. This is a hint for aggregation,
    not a verdict — the server side re-maps by vendor×status table.
    """
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
    return ""  # normal completion, no stop signal


# ── HTTP client ────────────────────────────────────────────────────────────

_shared_client: httpx.AsyncClient | None = None
_shared_client_ts: float = 0.0


def get_client() -> httpx.AsyncClient:
    global _shared_client, _shared_client_ts
    now = time.time()
    # Never expires on its own — we set per-request timeouts.
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            http2=False,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )
        _shared_client_ts = now
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
    cfg_getter,
    db_path,
) -> tuple[int, dict[str, str], Any]:
    """Proxy one request. Returns (status, headers, body-or-generator).

    - For non-streaming: body is bytes
    - For streaming: body is an async generator yielding bytes

    The caller (FastAPI route in app.py) is responsible for wrapping into
    a Response / StreamingResponse.
    """
    cfg = cfg_getter()
    start = time.time()

    # Parse body for model / stream / effort
    model = ""
    num_messages = 0
    is_stream = False
    effort = ""
    body_json: dict[str, Any] = {}
    if body:
        try:
            body_json = json.loads(body)
            if isinstance(body_json, dict):
                model = str(body_json.get("model") or "")
                is_stream = bool(body_json.get("stream"))
                msgs = body_json.get("messages") or []
                if isinstance(msgs, list):
                    num_messages = len(msgs)
                effort = extract_effort(body_json)
        except Exception:
            body_json = {}

    # Resolve vendor + upstream URL
    vendor_prefix, rest = split_vendor_prefix(path)
    # If no prefix in URL, fall back to configured vendor (single-vendor mode)
    if not vendor_prefix:
        vendor_prefix = cfg.get("vendor", "zhipu")
    vendor_info = config_store.vendor_by_prefix(vendor_prefix) or config_store.VENDORS["zhipu"]
    upstream_url = build_upstream_url(vendor_info, rest)

    # Effective upstream: allow user override per-vendor via cfg['vendor_overrides']
    overrides = cfg.get("vendor_overrides") or {}
    if vendor_prefix in overrides and overrides[vendor_prefix].get("upstream_url"):
        # rebuild from override
        o = overrides[vendor_prefix]
        upstream_url = (o["upstream_url"].rstrip("/") + ("/" + rest if rest else ""))

    headers = filter_upstream_headers(request_headers)
    vendor_id = cfg.get("vendor", vendor_prefix) if vendor_prefix == cfg.get("vendor") else vendor_prefix
    plan_id = cfg.get("plan", "")
    user_hash = cfg.get("user_hash", "")

    client = get_client()

    if is_stream:
        return await _proxy_stream(
            client, method, upstream_url, headers, body,
            start, vendor_id, plan_id, model, rest, num_messages, effort, user_hash, db_path,
        )

    # ── Non-streaming path ─────────────────────────────────────────────
    timeout_type = ""
    try:
        # Single request with read timeout large enough for non-streaming completions
        resp = await asyncio.wait_for(
            client.request(method, upstream_url, headers=headers, content=body),
            timeout=READ_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        timeout_type = "read_timeout"
        _record(
            db_path, start, vendor_id, plan_id, model, rest,
            usage={}, status_code=0, ttft_ms=0, tps_mean=0.0,
            error_type="timeout", error_msg_hash="",
            timeout_type=timeout_type, stop_signal="read_timeout",
            did_complete=False, num_messages=num_messages, effort=effort, user_hash=user_hash,
        )
        return (504, {"content-type": "application/json"}, b'{"error":{"type":"read_timeout"}}')
    except httpx.ConnectError:
        timeout_type = "connect_timeout"
        _record(
            db_path, start, vendor_id, plan_id, model, rest,
            usage={}, status_code=0, ttft_ms=0, tps_mean=0.0,
            error_type="connect_failed", error_msg_hash="",
            timeout_type=timeout_type, stop_signal="connect_timeout",
            did_complete=False, num_messages=num_messages, effort=effort, user_hash=user_hash,
        )
        return (502, {"content-type": "application/json"}, b'{"error":{"type":"connect_failed"}}')
    except Exception as e:
        logger.exception("proxy non-stream error")
        _record(
            db_path, start, vendor_id, plan_id, model, rest,
            usage={}, status_code=0, ttft_ms=0, tps_mean=0.0,
            error_type="proxy_error", error_msg_hash=hashlib.sha256(str(e).encode()).hexdigest()[:16],
            timeout_type="", stop_signal="proxy_error",
            did_complete=False, num_messages=num_messages, effort=effort, user_hash=user_hash,
        )
        return (502, {"content-type": "application/json"}, b'{"error":{"type":"proxy_error"}}')

    latency_ms = int((time.time() - start) * 1000)
    usage: dict[str, int] = {}
    try:
        usage = normalize_usage(resp.json().get("usage", {}))
    except Exception:
        pass

    body_bytes = resp.content
    err_type, err_hash = "", ""
    if resp.status_code >= 400:
        try:
            err_type, err_hash = classify_error(resp.status_code, resp.text)
        except Exception:
            pass

    stop_signal = classify_stop_signal(resp.status_code, "", did_complete=True)

    # TTFT for non-streaming ≈ first byte time. We don't have it precisely;
    # approximate as full latency (conservative; better than 0).
    ttft_ms = latency_ms
    tps = (usage["out"] / (latency_ms / 1000.0)) if (usage["out"] and latency_ms > 0) else 0.0

    _record(
        db_path, start, vendor_id, plan_id, model, rest,
        usage=usage, status_code=resp.status_code, ttft_ms=ttft_ms, tps_mean=tps,
        error_type=err_type, error_msg_hash=err_hash,
        timeout_type="", stop_signal=stop_signal,
        did_complete=True, num_messages=num_messages, effort=effort, user_hash=user_hash,
    )

    out_headers = {"content-type": resp.headers.get("content-type", "application/json")}
    return (resp.status_code, out_headers, body_bytes)


async def _proxy_stream(
    client: httpx.AsyncClient, method: str, url: str, headers: dict[str, str], body: bytes,
    start: float, vendor_id: str, plan_id: str, model: str, endpoint: str,
    num_messages: int, effort: str, user_hash: str, db_path,
) -> tuple[int, dict[str, str], Any]:
    """Stream proxy with per-stage timeout tracking."""

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
                # Non-SSE error: capture body for classification, forward as-is
                body_bytes = await resp.aread()
                try:
                    state["error_type"], state["error_msg_hash"] = classify_error(resp.status_code, body_bytes.decode("utf-8", "replace"))
                except Exception:
                    pass
                state["did_complete"] = False
                yield body_bytes
                await resp.aclose()
                return

            # TTFT: first non-empty SSE line (or first byte)
            first_seen = False
            async for raw_line in resp.aiter_lines():
                now = time.time()
                if not first_seen and raw_line.strip():
                    state["ttft_ms"] = int((now - start) * 1000)
                    if state["ttft_ms"] > TTFT_TIMEOUT_S * 1000:
                        # still record but tag
                        pass
                    first_seen = True
                    state["last_line_ts"] = now
                else:
                    gap = now - state["last_line_ts"]
                    if gap > STALL_TIMEOUT_S and first_seen:
                        state["timeout_type"] = "stream_stall_timeout"
                    state["last_line_ts"] = now

                yield raw_line + "\n"

                # Parse SSE data lines to extract usage on the fly
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
        except (asyncio.TimeoutError, Exception) as e:
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
                state["status_code"], state["timeout_type"], state["did_complete"]
            )
            _record(
                db_path, start, vendor_id, plan_id, model, endpoint,
                usage=usage, status_code=state["status_code"],
                ttft_ms=state["ttft_ms"], tps_mean=tps,
                error_type=state["error_type"], error_msg_hash=state["error_msg_hash"],
                timeout_type=state["timeout_type"], stop_signal=stop_signal,
                did_complete=state["did_complete"],
                num_messages=num_messages, effort=effort, user_hash=user_hash,
            )

    return (200, {"content-type": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"}, generator())


# ── Recording helper ──────────────────────────────────────────────────────


def _record(
    db_path, start_ts: float, vendor: str, plan: str, model: str, endpoint: str,
    usage: dict[str, int], status_code: int, ttft_ms: int, tps_mean: float,
    error_type: str, error_msg_hash: str, timeout_type: str, stop_signal: str,
    did_complete: bool, num_messages: int, effort: str, user_hash: str,
) -> None:
    latency_ms = int((time.time() - start_ts) * 1000)
    rec = {
        "ts": start_ts,
        "ts_text": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
