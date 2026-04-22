"""Gunicorn configuration for the Flask API server."""

import os

# ─── Server Socket ───────────────────────────────────────────────────
bind = f"0.0.0.0:{os.getenv('API_PORT', '5050')}"

# ─── Worker Processes ────────────────────────────────────────────────
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = "gthread"
threads = 20

# ─── Timeouts ────────────────────────────────────────────────────────
timeout = 0          # Disable timeout to prevent killing SSE streams
graceful_timeout = 30
keepalive = 5

# ─── Logging ─────────────────────────────────────────────────────────
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# ─── Process Naming ──────────────────────────────────────────────────
proc_name = "exxomatic-api"
