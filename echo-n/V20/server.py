"""
echo-n.V20.server — OCPP 2.0.1 echo server factory (echo-n context).

Provides ``create_v201_echo_server`` which spins up a WebSocket server
that delegates every message to ``core.V20.V201ChargePoint``.
Zero handler code lives here — it's all in ``core/V20/``.

Usage (standalone):
    python echo-n/main.py

Usage (programmatic / tests):
    server = await create_v201_echo_server("127.0.0.1", 0)
    port   = server.sockets[0].getsockname()[1]
"""

from __future__ import annotations

import logging

import websockets

from core.V20 import V201ChargePoint

logger = logging.getLogger(__name__)


async def _on_connect(connection):
    """Accept a 2.0.1 charger and start processing its messages."""
    path = connection.request.path
    charge_point_id = path.strip("/").split("/")[-1]

    logger.info(
        "Echo-N V201 — charger connected  id=%s  path=%s",
        charge_point_id,
        path,
    )

    cp = V201ChargePoint(charge_point_id, connection)

    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info("Echo-N V201 — charger disconnected  id=%s", charge_point_id)


async def create_v201_echo_server(
    host: str = "0.0.0.0",
    port: int = 5001,
) -> websockets.WebSocketServer:
    """
    Create and return an OCPP 2.0.1 echo WebSocket server (echo-n context).

    The server is already listening when this coroutine returns.
    Call ``server.close()`` + ``await server.wait_closed()`` to tear down.
    """
    server = await websockets.serve(
        _on_connect,
        host,
        port,
        subprotocols=["ocpp2.0.1"],
    )
    logger.info("Echo-N V201 server listening on %s:%d", host, port)
    return server
