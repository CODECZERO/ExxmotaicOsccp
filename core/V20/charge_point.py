"""
core.V20.charge_point — OCPP 2.0.1 ChargePoint (server-side).

Same pattern as V16 — subclass the ``ocpp`` library's ChargePoint and
delegate every @on handler to a pure function.
"""

from __future__ import annotations

import logging

from ocpp.routing import on
from ocpp.v201 import ChargePoint as _OcppV201CP
from ocpp.v201.enums import Action

from core.V20.boot_notification import handle_boot_notification
from core.V20.heartbeat import handle_heartbeat
from core.V20.status_notification import handle_status_notification
from core.V20.transaction_event import handle_transaction_event
from core.V20.meter_values import handle_meter_values
from core.V20.notify_event import handle_notify_event

logger = logging.getLogger(__name__)


class V201ChargePoint(_OcppV201CP):
    """
    Server-side representation of an OCPP 2.0.1 charging station.
    """

    # ── BootNotification ─────────────────────────────────────────────
    @on(Action.boot_notification)
    async def on_boot_notification(
        self, charging_station: dict, reason: str, **kwargs
    ):
        return handle_boot_notification(
            charging_station=charging_station,
            reason=reason,
            **kwargs,
        )

    # ── Heartbeat ────────────────────────────────────────────────────
    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        return handle_heartbeat(**kwargs)

    # ── StatusNotification ───────────────────────────────────────────
    @on(Action.status_notification)
    async def on_status_notification(
        self,
        timestamp: str,
        connector_status: str,
        evse_id: int,
        connector_id: int,
        **kwargs,
    ):
        return handle_status_notification(
            timestamp=timestamp,
            connector_status=connector_status,
            evse_id=evse_id,
            connector_id=connector_id,
            **kwargs,
        )

    # ── TransactionEvent ─────────────────────────────────────────────
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
        return handle_transaction_event(
            event_type=event_type,
            timestamp=timestamp,
            trigger_reason=trigger_reason,
            seq_no=seq_no,
            transaction_info=transaction_info,
            **kwargs,
        )

    # ── MeterValues ──────────────────────────────────────────────────
    @on(Action.meter_values)
    async def on_meter_values(self, evse_id: int, meter_value: list, **kwargs):
        return handle_meter_values(
            evse_id=evse_id,
            meter_value=meter_value,
            **kwargs,
        )

    # ── NotifyEvent ──────────────────────────────────────────────────
    @on(Action.notify_event)
    async def on_notify_event(
        self, generated_at: str, seq_no: int, event_data: list, **kwargs
    ):
        return handle_notify_event(
            generated_at=generated_at,
            seq_no=seq_no,
            event_data=event_data,
            **kwargs,
        )
