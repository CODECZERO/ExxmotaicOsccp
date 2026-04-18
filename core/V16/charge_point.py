"""core.V16.charge_point — OCPP 1.6J ChargePoint (server-side)."""

from __future__ import annotations

import asyncio
import logging

from ocpp.routing import on
from ocpp.v16 import ChargePoint as _OcppV16CP, call
from ocpp.v16.enums import Action

from core.V16.boot_notification import handle_boot_notification
from core.V16.heartbeat import handle_heartbeat
from core.V16.status_notification import handle_status_notification
from core.V16.authorize import handle_authorize
from core.V16.start_transaction import handle_start_transaction
from core.V16.stop_transaction import handle_stop_transaction
from core.V16.meter_values import handle_meter_values

logger = logging.getLogger(__name__)


class V16ChargePoint(_OcppV16CP):
    """Server-side representation of an OCPP 1.6J charge point."""

    @on(Action.boot_notification)
    async def on_boot_notification(
        self, charge_point_vendor: str, charge_point_model: str, **kwargs
    ):
        return await asyncio.to_thread(
            handle_boot_notification,
            charge_point_id=self.id,
            charge_point_vendor=charge_point_vendor,
            charge_point_model=charge_point_model,
            **kwargs,
        )

    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        return await asyncio.to_thread(handle_heartbeat, charge_point_id=self.id, **kwargs)

    @on(Action.status_notification)
    async def on_status_notification(
        self, connector_id: int, error_code: str, status: str, **kwargs
    ):
        return await asyncio.to_thread(
            handle_status_notification,
            charge_point_id=self.id,
            connector_id=connector_id,
            error_code=error_code,
            status=status,
            **kwargs,
        )

    @on(Action.authorize)
    async def on_authorize(self, id_tag: str, **kwargs):
        return await asyncio.to_thread(handle_authorize, id_tag=id_tag, **kwargs)

    @on(Action.start_transaction)
    async def on_start_transaction(
        self,
        connector_id: int,
        id_tag: str,
        meter_start: int,
        timestamp: str,
        **kwargs,
    ):
        return await asyncio.to_thread(
            handle_start_transaction,
            charge_point_id=self.id,
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=timestamp,
            **kwargs,
        )

    @on(Action.stop_transaction)
    async def on_stop_transaction(
        self, meter_stop: int, timestamp: str, transaction_id: int, **kwargs
    ):
        return await asyncio.to_thread(
            handle_stop_transaction,
            charge_point_id=self.id,
            meter_stop=meter_stop,
            timestamp=timestamp,
            transaction_id=transaction_id,
            **kwargs,
        )

    @on(Action.meter_values)
    async def on_meter_values(self, connector_id: int, meter_value: list, **kwargs):
        return await asyncio.to_thread(
            handle_meter_values,
            charge_point_id=self.id,
            connector_id=connector_id,
            meter_value=meter_value,
            **kwargs,
        )

    async def remote_start(self, id_tag: str, connector_id: int = 1) -> str:
        """Send RemoteStartTransaction to the charger."""
        request = call.RemoteStartTransaction(id_tag=id_tag, connector_id=connector_id)
        response = await self.call(request)
        return response.status

    async def remote_stop(self, transaction_id: int) -> str:
        """Send RemoteStopTransaction to the charger."""
        request = call.RemoteStopTransaction(transaction_id=transaction_id)
        response = await self.call(request)
        return response.status

    async def reset(self, reset_type: str = "Soft") -> str:
        """Send Reset command."""
        request = call.Reset(type=reset_type)
        response = await self.call(request)
        return response.status

    async def unlock(self, connector_id: int = 1) -> str:
        """Send UnlockConnector command."""
        request = call.UnlockConnector(connector_id=connector_id)
        response = await self.call(request)
        return response.status
