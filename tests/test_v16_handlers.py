"""tests.test_v16_handlers"""

from __future__ import annotations

from datetime import datetime

import pytest

from ocpp.v16.enums import AuthorizationStatus



@pytest.mark.asyncio
async def test_v16_heartbeat(v16_client):
    """Heartbeat response must contain a valid ISO 8601 UTC timestamp."""
    response = await v16_client.send_heartbeat()

    assert response.current_time is not None
    # Verify it parses as a valid ISO datetime
    parsed = datetime.fromisoformat(response.current_time)
    assert parsed.year >= 2025



@pytest.mark.asyncio
async def test_v16_authorize(v16_client):
    """Echo server accepts any RFID tag — id_tag_info.status must be Accepted."""
    response = await v16_client.send_authorize(id_tag="RFID_TEST_001")

    assert response.id_tag_info["status"] == AuthorizationStatus.accepted



@pytest.mark.asyncio
async def test_v16_start_transaction(v16_client):
    """StartTransaction must return:"""
    response = await v16_client.send_start_transaction(
        connector_id=1,
        id_tag="RFID_TEST_001",
        meter_start=0,
    )

    assert response.transaction_id >= 1
    assert response.id_tag_info["status"] == AuthorizationStatus.accepted



@pytest.mark.asyncio
async def test_v16_stop_transaction(v16_client):
    """
    StopTransaction must return a valid (possibly empty) response.
    The echo server just ACKs — no id_tag_info required.
    """
    # First start a transaction to get a valid tx_id
    start_resp = await v16_client.send_start_transaction()
    tx_id = start_resp.transaction_id

    response = await v16_client.send_stop_transaction(
        transaction_id=tx_id,
        meter_stop=5000,
    )

    # StopTransaction response may have an optional id_tag_info.
    # Echo server returns empty — we just assert it didn't error.
    assert response is not None



@pytest.mark.asyncio
async def test_v16_status_notification(v16_client):
    """StatusNotification returns an empty ACK — just verify no error."""
    response = await v16_client.send_status_notification(
        connector_id=1,
        error_code="NoError",
        status="Available",
    )

    # StatusNotification response is an empty object — just assert it exists.
    assert response is not None



@pytest.mark.asyncio
async def test_v16_meter_values(v16_client):
    """MeterValues returns an empty ACK — just verify no error."""
    response = await v16_client.send_meter_values(
        connector_id=1,
        meter_value=[{
            "timestamp": "2026-04-13T12:00:00+00:00",
            "sampled_value": [
                {"value": "1500", "measurand": "Energy.Active.Import.Register"},
                {"value": "7200", "measurand": "Power.Active.Import"},
            ],
        }],
    )

    assert response is not None
