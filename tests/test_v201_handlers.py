"""tests.test_v201_handlers"""

from __future__ import annotations

from datetime import datetime

import pytest

from ocpp.v201.enums import RegistrationStatusEnumType



@pytest.mark.asyncio
async def test_v201_heartbeat(v201_client):
    """Heartbeat response must contain a valid ISO 8601 UTC timestamp."""
    response = await v201_client.send_heartbeat()

    assert response.current_time is not None
    parsed = datetime.fromisoformat(response.current_time)
    assert parsed.year >= 2025



@pytest.mark.asyncio
async def test_v201_status_notification(v201_client):
    """StatusNotification returns an empty ACK — just verify no error."""
    response = await v201_client.send_status_notification(
        evse_id=1,
        connector_id=1,
        connector_status="Available",
    )

    assert response is not None



@pytest.mark.asyncio
async def test_v201_transaction_event(v201_client):
    """
    TransactionEvent (Started) returns an empty ACK.
    Verify the server handles the full payload without error.
    """
    response = await v201_client.send_transaction_event(
        event_type="Started",
        trigger_reason="CablePluggedIn",
        seq_no=0,
        transaction_id="TX_INTEG_001",
    )

    assert response is not None



@pytest.mark.asyncio
async def test_v201_meter_values(v201_client):
    """MeterValues returns an empty ACK — just verify no error."""
    response = await v201_client.send_meter_values(
        evse_id=1,
        meter_value=[{
            "timestamp": "2026-04-13T12:00:00+00:00",
            "sampled_value": [{"value": 1500.0}],
        }],
    )

    assert response is not None



@pytest.mark.asyncio
async def test_v201_notify_event(v201_client):
    """
    NotifyEvent with a hardware event payload returns an empty ACK.
    Verifies the full event_data structure is accepted by the server.
    """
    response = await v201_client.send_notify_event(seq_no=0)

    assert response is not None
