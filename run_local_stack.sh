#!/bin/bash

# Load env variables safely
set -a
source ./test.env
set +a
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "--- Stopping any old processes ---"
pkill -f "python.*main"
sleep 2

echo "--- Initializing Local DB ---"
./venv/bin/python init_db.py

echo "--- Starting Services ---"

# 1. API Server (5050)
./venv/bin/python -m api.main > api.log 2>&1 &
echo "Started API Server..."

# 2. Production Core (5000)
./venv/bin/python -m core.main > core.log 2>&1 &
echo "Started Core Server..."

# 3. Echo Server (8000)
./venv/bin/python -m echo.main > echo.log 2>&1 &
echo "Started Echo Server..."

# 4. Echo-N Server (5001)
# echo-n contains a hyphen, so we run the file directly
./venv/bin/python echo-n/main.py > echo_n.log 2>&1 &
echo "Started Echo-N Server..."

echo "Waiting for services to warm up (5s)..."
sleep 5

echo "--- Running Local Validation ---"
./venv/bin/python test_local.py

echo "--- Shutting down services ---"
pkill -f "python.*main"

echo "Done."
