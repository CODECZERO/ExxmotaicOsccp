"""echo.V20.server — OCPP 2.0.1 echo server factory."""

from __future__ import annotations

import logging

import websockets

from core.V20 import V201ChargePoint
from shared.constants import OCPP_V201_SUBPROTOCOL

logger = logging.getLogger(__name__)


async def _on_connect(connection):
    """Accept a 2.0.1 charger and start processing its messages."""
    path = connection.request.path
    charge_point_id = path.strip("/").split("/")[-1]

    logger.info(
        "Echo V201 — charger connected  id=%s  path=%s",
        charge_point_id,
        path,
    )

    cp = V201ChargePoint(charge_point_id, connection)

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Echo V201 — charger disconnected  id=%s", charge_point_id)


async def create_v201_echo_server(
    host: str = "0.0.0.0",
    port: int = 8001,
) -> websockets.WebSocketServer:
    """Create and return an OCPP 2.0.1 echo WebSocket server."""
    server = await websockets.serve(
        _on_connect,
        host,
        port,
        subprotocols=[OCPP_V201_SUBPROTOCOL],
    )
    logger.info("Echo V201 server listening on %s:%d", host, port)
    return server
