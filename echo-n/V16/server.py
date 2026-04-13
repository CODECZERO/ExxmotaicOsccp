"""
echo-n.V16.server — OCPP 1.6J echo server factory (echo-n context).

Same pattern as ``echo/V16/server.py`` but intended for the echo-n
debug server.  All handler logic is in ``core/V16/``.

Usage (programmatic / tests):
    server = await create_v16_echo_server("127.0.0.1", 0)
    port   = server.sockets[0].getsockname()[1]
"""

from __future__ import annotations

import logging

import websockets

from core.V16 import V16ChargePoint

logger = logging.getLogger(__name__)


async def _on_connect(connection):
    """Accept a 1.6J charger and start processing its messages."""
    path = connection.request.path
    charge_point_id = path.strip("/").split("/")[-1]

    logger.info(
        "Echo-N V16 — charger connected  id=%s  path=%s",
        charge_point_id,
        path,
    )

    cp = V16ChargePoint(charge_point_id, connection)

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Echo-N V16 — charger disconnected  id=%s", charge_point_id)


async def create_v16_echo_server(
    host: str = "0.0.0.0",
    port: int = 5002,
) -> websockets.WebSocketServer:
    """
    Create and return an OCPP 1.6J echo WebSocket server (echo-n context).

    The server is already listening when this coroutine returns.
    Call ``server.close()`` + ``await server.wait_closed()`` to tear down.
    """
    server = await websockets.serve(
        _on_connect,
        host,
        port,
        subprotocols=["ocpp1.6"],
    )
    logger.info("Echo-N V16 server listening on %s:%d", host, port)
    return server
