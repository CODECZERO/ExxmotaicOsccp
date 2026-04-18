#!/bin/bash
set -e

echo "──────────────────────────────────────────────"
echo "  Exxomatic API Server — Starting"
echo "──────────────────────────────────────────────"

# Run database migrations / table creation
echo "[init] Running database initialization..."
python init_db.py || echo "[warn] DB init skipped or failed — continuing"

# Start Gunicorn
echo "[start] Launching Gunicorn on port ${API_PORT:-5050}..."
exec gunicorn \
  --config server/gunicorn.conf.py \
  "api:create_app()"
