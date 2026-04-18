"""core.V20.charge_point — OCPP 2.0.1 ChargePoint (server-side)."""

from __future__ import annotations

import asyncio
import logging

from ocpp.routing import on
from ocpp.v201 import ChargePoint as _OcppV201CP, call
from ocpp.v201.enums import Action

from core.V20.boot_notification import handle_boot_notification
from core.V20.heartbeat import handle_heartbeat
from core.V20.status_notification import handle_status_notification
from core.V20.transaction_event import handle_transaction_event
from core.V20.meter_values import handle_meter_values
from core.V20.notify_event import handle_notify_event

logger = logging.getLogger(__name__)


class V201ChargePoint(_OcppV201CP):
    """Server-side representation of an OCPP 2.0.1 charging station."""

    @on(Action.boot_notification)
    async def on_boot_notification(
        self, charging_station: dict, reason: str, **kwargs
    ):
        return await asyncio.to_thread(
            handle_boot_notification,
            charge_point_id=self.id,
            charging_station=charging_station,
            reason=reason,
            **kwargs,
        )

    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        return await asyncio.to_thread(handle_heartbeat, charge_point_id=self.id, **kwargs)

    @on(Action.status_notification)
    async def on_status_notification(
        self,
        timestamp: str,
        connector_status: str,
        evse_id: int,
        connector_id: int,
        **kwargs,
    ):
        return await asyncio.to_thread(
            handle_status_notification,
            charge_point_id=self.id,
            timestamp=timestamp,
            connector_status=connector_status,
            evse_id=evse_id,
            connector_id=connector_id,
            **kwargs,
        )

    @on(Action.transaction_event)
    async def on_transaction_event(
        self,
        event_type: str,
        timestamp: str,
        trigger_reason: str,
        seq_no: int,
        transaction_info: dict,
        **kwargs,
    ):
        return await asyncio.to_thread(
            handle_transaction_event,
            charge_point_id=self.id,
            event_type=event_type,
            timestamp=timestamp,
            trigger_reason=trigger_reason,
            seq_no=seq_no,
            transaction_info=transaction_info,
            **kwargs,
        )

    @on(Action.meter_values)
    async def on_meter_values(self, evse_id: int, meter_value: list, **kwargs):
        return await asyncio.to_thread(
            handle_meter_values,
            charge_point_id=self.id,
            evse_id=evse_id,
            meter_value=meter_value,
            **kwargs,
        )

    @on(Action.notify_event)
    async def on_notify_event(
        self, generated_at: str, seq_no: int, event_data: list, **kwargs
    ):
        return await asyncio.to_thread(
            handle_notify_event,
            charge_point_id=self.id,
            generated_at=generated_at,
            seq_no=seq_no,
            event_data=event_data,
            **kwargs,
        )

    async def request_start(self, id_tag: str, evse_id: int = 1) -> str:
        """Send RequestStartTransaction to the station."""
        import random
        # OCPP 2.0.1 requires remoteStartId to track the request
        remote_id = random.randint(1, 999999)
        request = call.RequestStartTransaction(
            remote_start_id=remote_id,
            id_token={"idToken": id_tag, "type": "ISO14443"},
            evse_id=evse_id
        )
        response = await self.call(request)
        return response.status

    async def request_stop(self, transaction_id: str) -> str:
        """Send RequestStopTransaction to the station."""
        request = call.RequestStopTransaction(transaction_id=transaction_id)
        response = await self.call(request)
        return response.status

    async def reset(self, reset_type: str = "OnIdle") -> str:
        """Send Reset command."""
        request = call.Reset(type=reset_type)
        response = await self.call(request)
        return response.status

    async def unlock(self, evse_id: int = 1, connector_id: int = 1) -> str:
        """Send UnlockConnector command."""
        request = call.UnlockConnector(evse_id=evse_id, connector_id=connector_id)
        response = await self.call(request)
        return response.status
