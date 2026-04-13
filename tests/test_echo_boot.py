"""
tests.test_echo_boot
~~~~~~~~~~~~~~~~~~~~

Integration test:  validates that both OCPP 1.6J and 2.0.1 echo servers
correctly handle a BootNotification round-trip over a real WebSocket.

Both versions reuse handler code from ``core/V16/`` and ``core/V20/``
via the echo server factories.

Run:
    pytest tests/test_echo_boot.py -v
"""

from __future__ import annotations

import asyncio
import sys
import os

import pytest
import websockets

# Ensure project root is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── V16 imports ──────────────────────────────────────────────────────
from ocpp.v16 import ChargePoint as V16ClientCP         # noqa: E402
from ocpp.v16 import call as v16_call                   # noqa: E402
from ocpp.v16 import call_result as v16_call_result     # noqa: E402
from ocpp.v16.enums import RegistrationStatus           # noqa: E402

# ── V201 imports ─────────────────────────────────────────────────────
from ocpp.v201 import ChargePoint as V201ClientCP       # noqa: E402
from ocpp.v201 import call as v201_call                 # noqa: E402
from ocpp.v201 import call_result as v201_call_result   # noqa: E402
from ocpp.v201.enums import RegistrationStatusEnumType  # noqa: E402

# ── Server factories (the code under test) ───────────────────────────
from echo.V16.server import create_v16_echo_server      # noqa: E402
from echo.V20.server import create_v201_echo_server     # noqa: E402


# ── helpers ──────────────────────────────────────────────────────────

class _V16TestClient(V16ClientCP):
    """Minimal V16 client that can send a BootNotification."""

    async def send_boot_notification(self) -> v16_call_result.BootNotification:
        request = v16_call.BootNotification(
            charge_point_model="DC-60kW",
            charge_point_vendor="TKT",
        )
        return await self.call(request)


class _V201TestClient(V201ClientCP):
    """Minimal V201 client that can send a BootNotification."""

    async def send_boot_notification(self) -> v201_call_result.BootNotification:
        request = v201_call.BootNotification(
            charging_station={"vendor_name": "TKT", "model": "DC-60kW"},
            reason="PowerUp",
        )
        return await self.call(request)


# ── test ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_echo_boot_notification_both_versions():
    """
    Full round-trip for BOTH protocol versions over real WebSockets.

    1. Start V16 echo server → client sends BootNotification → assert Accepted.
    2. Start V201 echo server → client sends BootNotification → assert Accepted.

    This single test validates that core/V16 and core/V20 handler code
    works correctly when consumed through the echo server factories.
    """
    # ── V16 round-trip ───────────────────────────────────────────────
    v16_server = await create_v16_echo_server("127.0.0.1", 0)
    v16_port = v16_server.sockets[0].getsockname()[1]

    try:
        url = f"ws://127.0.0.1:{v16_port}/ocpp/1.6/TEST_V16"
        async with websockets.connect(url, subprotocols=["ocpp1.6"]) as ws:
            client = _V16TestClient("TEST_V16", ws)
            start_task = asyncio.create_task(client.start())

            response = await client.send_boot_notification()

            assert response.status == RegistrationStatus.accepted, (
                f"V16 BootNotification expected Accepted, got {response.status}"
            )
            assert response.interval == 10
            assert response.current_time is not None

            start_task.cancel()
    finally:
        v16_server.close()
        await v16_server.wait_closed()

    # ── V201 round-trip ──────────────────────────────────────────────
    v201_server = await create_v201_echo_server("127.0.0.1", 0)
    v201_port = v201_server.sockets[0].getsockname()[1]

    try:
        url = f"ws://127.0.0.1:{v201_port}/ocpp/2.0.1/TEST_V201"
        async with websockets.connect(url, subprotocols=["ocpp2.0.1"]) as ws:
            client = _V201TestClient("TEST_V201", ws)
            start_task = asyncio.create_task(client.start())

            response = await client.send_boot_notification()

            assert response.status == RegistrationStatusEnumType.accepted, (
                f"V201 BootNotification expected Accepted, got {response.status}"
            )
            assert response.interval == 10
            assert response.current_time is not None

            start_task.cancel()
    finally:
        v201_server.close()
        await v201_server.wait_closed()
