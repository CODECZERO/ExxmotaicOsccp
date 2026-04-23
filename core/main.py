"""core.main — Dual-version OCPP WebSocket server."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import websockets

# Ensure the project root is importable when running as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.env import load_env  # noqa: E402

load_env()

from shared.constants import CORE_PORT, BIND_HOST, LOG_LEVEL   # noqa: E402
from core.router import detect_version, get_subprotocols, create_charge_point
from core.dispatcher import active_connections, start_command_poller   # noqa: E402

from shared.logger import setup_logging

setup_logging("ocpp-core", LOG_LEVEL)
logger = logging.getLogger("core.main")


async def on_connect(connection):
    """Handle every new WebSocket connection."""
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
    active_connections[charge_point_id] = cp

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Charger disconnected  id=%s", charge_point_id)
    finally:
        active_connections.pop(charge_point_id, None)


async def main():
    server = await websockets.serve(
        on_connect,
        BIND_HOST,
        CORE_PORT,
        subprotocols=get_subprotocols(),
    )
    
    # Start the command poller as a background task
    asyncio.create_task(start_command_poller())
    logger.info(
        "OCPP Core server listening on %s:%d  (1.6 + 2.0.1)",
        BIND_HOST,
        CORE_PORT,
    )
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
