"""tests.conftest — Shared pytest fixtures for OCPP integration tests."""

from __future__ import annotations

import asyncio
import sys
import os
from datetime import datetime, timezone

import pytest
import pytest_asyncio
import websockets

# Ensure project root is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v16 import ChargePoint as _V16ClientCP       # noqa: E402
from ocpp.v16 import call as v16_call                  # noqa: E402
from ocpp.v16 import call_result as v16_call_result    # noqa: E402
from ocpp.v16.enums import (                           # noqa: E402
    ChargePointErrorCode,
    ChargePointStatus,
)

from ocpp.v201 import ChargePoint as _V201ClientCP     # noqa: E402
from ocpp.v201 import call as v201_call                # noqa: E402
from ocpp.v201 import call_result as v201_call_result  # noqa: E402
from ocpp.v201.enums import (                          # noqa: E402
    ConnectorStatusEnumType,
    TransactionEventEnumType,
    TriggerReasonEnumType,
)

from echo.V16.server import create_v16_echo_server     # noqa: E402
from echo.V20.server import create_v201_echo_server    # noqa: E402



class V16TestClient(_V16ClientCP):
    """
    Full-featured V16 test client.

    Exposes a send method for every message type the V16 echo server handles.
    """

    async def send_boot_notification(self) -> v16_call_result.BootNotification:
        return await self.call(v16_call.BootNotification(
            charge_point_model="DC-60kW",
            charge_point_vendor="TKT",
        ))

    async def send_heartbeat(self) -> v16_call_result.Heartbeat:
        return await self.call(v16_call.Heartbeat())

    async def send_authorize(self, id_tag: str = "RFID_TEST_001") -> v16_call_result.Authorize:
        return await self.call(v16_call.Authorize(id_tag=id_tag))

    async def send_start_transaction(
        self,
        connector_id: int = 1,
        id_tag: str = "RFID_TEST_001",
        meter_start: int = 0,
    ) -> v16_call_result.StartTransaction:
        return await self.call(v16_call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        ))

    async def send_stop_transaction(
        self,
        transaction_id: int = 1,
        meter_stop: int = 5000,
    ) -> v16_call_result.StopTransaction:
        return await self.call(v16_call.StopTransaction(
            meter_stop=meter_stop,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            transaction_id=transaction_id,
        ))

    async def send_status_notification(
        self,
        connector_id: int = 1,
        error_code: str = ChargePointErrorCode.no_error,
        status: str = ChargePointStatus.available,
    ) -> v16_call_result.StatusNotification:
        return await self.call(v16_call.StatusNotification(
            connector_id=connector_id,
            error_code=error_code,
            status=status,
        ))

    async def send_meter_values(
        self,
        connector_id: int = 1,
        meter_value: list | None = None,
    ) -> v16_call_result.MeterValues:
        if meter_value is None:
            meter_value = [{
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "sampled_value": [{"value": "1500", "measurand": "Energy.Active.Import.Register"}],
            }]
        return await self.call(v16_call.MeterValues(
            connector_id=connector_id,
            meter_value=meter_value,
        ))



class V201TestClient(_V201ClientCP):
    """
    Full-featured V201 test client.

    Exposes a send method for every message type the V201 echo server handles.
    """

    async def send_boot_notification(self) -> v201_call_result.BootNotification:
        return await self.call(v201_call.BootNotification(
            charging_station={"vendor_name": "TKT", "model": "DC-60kW"},
            reason="PowerUp",
        ))

    async def send_heartbeat(self) -> v201_call_result.Heartbeat:
        return await self.call(v201_call.Heartbeat())

    async def send_status_notification(
        self,
        evse_id: int = 1,
        connector_id: int = 1,
        connector_status: str = ConnectorStatusEnumType.available,
    ) -> v201_call_result.StatusNotification:
        return await self.call(v201_call.StatusNotification(
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            connector_status=connector_status,
            evse_id=evse_id,
            connector_id=connector_id,
        ))

    async def send_transaction_event(
        self,
        event_type: str = TransactionEventEnumType.started,
        trigger_reason: str = TriggerReasonEnumType.cable_plugged_in,
        seq_no: int = 0,
        transaction_id: str = "TX_TEST_001",
    ) -> v201_call_result.TransactionEvent:
        return await self.call(v201_call.TransactionEvent(
            event_type=event_type,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            trigger_reason=trigger_reason,
            seq_no=seq_no,
            transaction_info={"transaction_id": transaction_id},
        ))

    async def send_meter_values(
        self,
        evse_id: int = 1,
        meter_value: list | None = None,
    ) -> v201_call_result.MeterValues:
        if meter_value is None:
            meter_value = [{
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "sampled_value": [{"value": 1500.0}],
            }]
        return await self.call(v201_call.MeterValues(
            evse_id=evse_id,
            meter_value=meter_value,
        ))

    async def send_notify_event(
        self,
        seq_no: int = 0,
    ) -> v201_call_result.NotifyEvent:
        return await self.call(v201_call.NotifyEvent(
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            seq_no=seq_no,
            event_data=[{
                "event_id": 1,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "trigger": "Alerting",
                "actual_value": "42",
                "event_notification_type": "HardWiredNotification",
                "component": {"name": "Connector", "instance": "1"},
                "variable": {"name": "CurrentImport"},
            }],
        ))



@pytest_asyncio.fixture
async def v16_server():
    """Spin up a V16 echo server on a random free port, yield it, then tear down."""
    server = await create_v16_echo_server("127.0.0.1", 0)
    yield server
    server.close()
    await server.wait_closed()


@pytest_asyncio.fixture
async def v16_client(v16_server):
    """Connect a V16 test client to the running server."""
    port = v16_server.sockets[0].getsockname()[1]
    url = f"ws://127.0.0.1:{port}/ocpp/1.6/TEST_V16"
    async with websockets.connect(url, subprotocols=["ocpp1.6"]) as ws:
        client = V16TestClient("TEST_V16", ws)
        start_task = asyncio.create_task(client.start())
        try:
            yield client
        finally:
            start_task.cancel()


@pytest_asyncio.fixture
async def v201_server():
    """Spin up a V201 echo server on a random free port, yield it, then tear down."""
    server = await create_v201_echo_server("127.0.0.1", 0)
    yield server
    server.close()
    await server.wait_closed()


@pytest_asyncio.fixture
async def v201_client(v201_server):
    """Connect a V201 test client to the running server."""
    port = v201_server.sockets[0].getsockname()[1]
    url = f"ws://127.0.0.1:{port}/ocpp/2.0.1/TEST_V201"
    async with websockets.connect(url, subprotocols=["ocpp2.0.1"]) as ws:
        client = V201TestClient("TEST_V201", ws)
        start_task = asyncio.create_task(client.start())
        try:
            yield client
        finally:
            start_task.cancel()
