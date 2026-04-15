"""core.V20.notify_event — NotifyEvent handler (OCPP 2.0.1)."""

from __future__ import annotations

import logging

from ocpp.v201 import call_result

logger = logging.getLogger(__name__)


def handle_notify_event(
    charge_point_id: str = "",
    generated_at: str = "",
    seq_no: int = 0,
    event_data: list = None,
    **kwargs,
) -> call_result.NotifyEvent:
    """Log the event and acknowledge."""
    if event_data is None:
        event_data = []

    logger.info(
        "NotifyEvent  id=%s  generated_at=%s  seq=%d  events=%d  extras=%s",
        charge_point_id,
        generated_at,
        seq_no,
        len(event_data),
        kwargs,
    )
    return call_result.NotifyEvent()
