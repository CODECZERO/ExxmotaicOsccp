"""Gunicorn configuration for the Flask API server."""

import os

# ─── Server Socket ───────────────────────────────────────────────────
bind = f"0.0.0.0:{os.getenv('API_PORT', '5050')}"

# ─── Worker Processes ────────────────────────────────────────────────
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "gthread"
threads = 20

# ─── Timeouts ────────────────────────────────────────────────────────
timeout = 0          # Disable timeout to prevent killing SSE streams
graceful_timeout = 30
keepalive = 5

# ─── Logging ─────────────────────────────────────────────────────────
_log_dir = os.getenv("LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs"))
os.makedirs(_log_dir, exist_ok=True)

accesslog = os.path.join(_log_dir, "api-access.log")
errorlog = os.path.join(_log_dir, "api-error.log")
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# ─── Process Naming ──────────────────────────────────────────────────
proc_name = "exxomatic-api"
