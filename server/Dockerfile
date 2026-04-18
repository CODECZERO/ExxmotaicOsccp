# ═══════════════════════════════════════════════════════════════════════
#  Exxomatic API Server — Dockerfile
#  Flask REST API + Gunicorn for production
# ═══════════════════════════════════════════════════════════════════════

FROM python:3.12-slim AS server

# ─── System deps ─────────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── Python deps (cached layer) ─────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Application code ───────────────────────────────────────────────
COPY api/          api/
COPY core/         core/
COPY shared/       shared/
COPY server/       server/
COPY echo/         echo/
COPY echo-n/       echo-n/
COPY init_db.py    .
COPY .env.example  .env.example

# ─── Runtime ─────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIND_HOST=0.0.0.0 \
    API_PORT=5050

EXPOSE 5050

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5050/api/health || exit 1

ENTRYPOINT ["bash", "server/entrypoint.sh"]
