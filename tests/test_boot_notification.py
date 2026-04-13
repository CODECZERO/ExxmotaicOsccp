"""
tests.test_boot_notification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration test:  spins up the V16 echo server on a free port,
connects a client-side ChargePoint, sends a BootNotification,
and asserts the response is Accepted.

Run:
    pytest tests/test_boot_notification.py -v
"""

from __future__ import annotations

import asyncio
import sys
import os

import pytest
import websockets

# Ensure project root is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v16 import ChargePoint as ClientChargePoint  # noqa: E402
from ocpp.v16 import call, call_result                 # noqa: E402
from ocpp.v16.enums import RegistrationStatus          # noqa: E402

from core.V16 import V16ChargePoint                    # noqa: E402


# ── helpers ──────────────────────────────────────────────────────────

class _TestClient(ClientChargePoint):
    """Minimal client that can send a BootNotification."""

    async def send_boot_notification(self) -> call_result.BootNotification:
        request = call.BootNotification(
            charge_point_model="DC-60kW",
            charge_point_vendor="TKT",
        )
        return await self.call(request)


async def _echo_handler(connection):
    """Server-side handler identical to ``echo/main.py``."""
    cp_id = connection.request.path.strip("/").split("/")[-1]
    cp = V16ChargePoint(cp_id, connection)
    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        pass


# ── test ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_v16_boot_notification_accepted():
    """
    Full round-trip: server ↔ client over a real WebSocket.

    1. Start the echo server on port 0 (OS picks a free port).
    2. Connect a client and send BootNotification.
    3. Assert the server replies with status=Accepted.
    """
    # 1. start server
    server = await websockets.serve(
        _echo_handler,
        "127.0.0.1",
        0,                          # OS assigns a free port
        subprotocols=["ocpp1.6"],
    )
    port = server.sockets[0].getsockname()[1]

    try:
        # 2. connect client
        url = f"ws://127.0.0.1:{port}/ocpp/1.6/TEST001"
        async with websockets.connect(url, subprotocols=["ocpp1.6"]) as ws:
            client = _TestClient("TEST001", ws)

            # start() listens for incoming messages; we run it in parallel
            # with the BootNotification call.
            start_task = asyncio.create_task(client.start())

            response = await client.send_boot_notification()

            # 3. assertions
            assert response.status == RegistrationStatus.accepted
            assert response.interval == 10
            assert response.current_time is not None

            start_task.cancel()
    finally:
        server.close()
        await server.wait_closed()
