"""
echo.V16.server — OCPP 1.6J echo server factory.

Provides ``create_v16_echo_server`` which spins up a WebSocket server
that delegates every message to ``core.V16.V16ChargePoint``.
Zero handler code lives here — it's all in ``core/V16/``.

Usage (standalone):
    python echo/main.py

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
    port: int = 8000,
) -> websockets.WebSocketServer:
    """
    Create and return an OCPP 1.6J echo WebSocket server.

    The server is already listening when this coroutine returns.
    Call ``server.close()`` + ``await server.wait_closed()`` to tear down.
    """
    server = await websockets.serve(
        _on_connect,
        host,
        port,
        subprotocols=["ocpp1.6"],
    )
    logger.info("Echo V16 server listening on %s:%d", host, port)
    return server
