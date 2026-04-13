"""
core.main — Dual-version OCPP WebSocket server (:5000).

Accepts both 1.6J and 2.0.1 chargers on a single port.
The version is detected from the WebSocket request path and the
appropriate ChargePoint class is instantiated via ``router``.

Usage:
    python -m core.main
    # or
    python core/main.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import websockets

# Ensure the project root is importable when running as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.router import detect_version, get_subprotocols, create_charge_point  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("core.main")

CORE_PORT = int(os.getenv("CORE_PORT", "5000"))


async def on_connect(connection):
    """
    Handle every new WebSocket connection.

    1. Extract the charge-point id from the path.
    2. Detect the OCPP version from the path.
    3. Instantiate the matching ChargePoint subclass.
    4. Listen for messages until the charger disconnects.
    """
    path = connection.request.path
    charge_point_id = path.strip("/").split("/")[-1]
    version = detect_version(path)

    logger.info(
        "Charger connected  id=%s  version=%s  path=%s",
        charge_point_id,
        version,
        path,
    )

    cp = create_charge_point(charge_point_id, connection, version)

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Charger disconnected  id=%s", charge_point_id)


async def main():
    server = await websockets.serve(
        on_connect,
        "0.0.0.0",
        CORE_PORT,
        subprotocols=get_subprotocols(),
    )
    logger.info("OCPP Core server listening on :%d  (1.6 + 2.0.1)", CORE_PORT)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
