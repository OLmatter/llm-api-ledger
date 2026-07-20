"""
Project-wide constants (no magic numbers scattered in code).
"""

# ── HTTP / Proxy timeouts (seconds) ──
CONNECT_TIMEOUT_S = 5.0      # TCP connect — should never exceed this
READ_TIMEOUT_S = 30.0        # no bytes at all after connect
TTFT_TIMEOUT_S = 15.0        # first token not seen
STALL_TIMEOUT_S = 5.0        # gap between SSE chunks

# ── Dashboard defaults ──
DASHBOARD_WINDOW_DAYS = 30   # aggregate window for hero cards
HOURLY_CHART_HOURS = 24      # 24h chart
DAILY_CHART_DAYS = 7         # 7d chart
RECENT_LIMIT = 50            # recent requests table row cap

# ── Monitor loop ──
MONITOR_MIN_INTERVAL_S = 60  # floor — don't hammer vendor API
MONITOR_FAILURE_PAUSE_S = 900  # pause after 5 consecutive failures
MONITOR_FAILURE_STREAK = 5   # threshold for pause

# ── HTTP client ──
MAX_CONNECTIONS = 50
MAX_KEEPALIVE_CONNECTIONS = 10

# ── Export ──
EXPORT_MAX_DAYS = 90
EXPORT_DEFAULT_DAYS = 7
EXPORT_RAW_JSON_LIMIT = 4000  # truncate raw_json stored in DB

# ── CDN ──
CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
