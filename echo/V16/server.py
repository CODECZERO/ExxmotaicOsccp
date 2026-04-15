"""echo.V16.server — OCPP 1.6J echo server factory."""

from __future__ import annotations

import logging

import websockets

from core.V16 import V16ChargePoint
from shared.constants import OCPP_V16_SUBPROTOCOL, ECHO_PORT

logger = logging.getLogger(__name__)


async def _on_connect(connection):
    """Accept a 1.6J charger and start processing its messages."""
    path = connection.request.path
    charge_point_id = path.strip("/").split("/")[-1]

    logger.info(
        "Echo V16 — charger connected  id=%s  path=%s",
        charge_point_id,
        path,
    )

    cp = V16ChargePoint(charge_point_id, connection)

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Echo V16 — charger disconnected  id=%s", charge_point_id)


async def create_v16_echo_server(
    host: str = "0.0.0.0",
    port: int = ECHO_PORT,
) -> websockets.WebSocketServer:
    """Create and return an OCPP 1.6J echo WebSocket server."""
    server = await websockets.serve(
        _on_connect,
        host,
        port,
        subprotocols=[OCPP_V16_SUBPROTOCOL],
    )
    logger.info("Echo V16 server listening on %s:%d", host, port)
    return server
