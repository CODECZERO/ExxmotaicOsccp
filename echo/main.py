"""echo — Dual-version OCPP debug echo server."""

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

from shared.constants import (  # noqa: E402
    ECHO_PORT,
    BIND_HOST,
    LOG_LEVEL,
    OCPP_V16_SUBPROTOCOL,
    OCPP_V201_SUBPROTOCOL,
)
from core.router import detect_version, create_charge_point  # noqa: E402
from core.dispatcher import active_connections, start_command_poller  # noqa: E402

from shared.logger import setup_logging

setup_logging("ocpp-echo", LOG_LEVEL)
logger = logging.getLogger("echo")


async def _on_connect(connection):
    """Accept any OCPP charger, detect version, delegate to core."""
    path = connection.request.path
    charge_point_id = path.strip("/").split("/")[-1]
    version = detect_version(path)

    logger.info(
        "Echo — charger connected  id=%s  version=%s  path=%s",
        charge_point_id,
        version,
        path,
    )

    cp = create_charge_point(charge_point_id, connection, version)
    active_connections[charge_point_id] = cp

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Echo — charger disconnected  id=%s", charge_point_id)
    finally:
        active_connections.pop(charge_point_id, None)


async def main():
    server = await websockets.serve(
        _on_connect,
        BIND_HOST,
        ECHO_PORT,
        subprotocols=[OCPP_V16_SUBPROTOCOL, OCPP_V201_SUBPROTOCOL],
    )
    # Start the command poller as a background task
    asyncio.create_task(start_command_poller())
    logger.info(
        "Echo server ready on %s:%d  (V16 + V201 dual-version)",
        BIND_HOST,
        ECHO_PORT,
    )
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
