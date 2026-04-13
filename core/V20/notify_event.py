"""
core.V20.notify_event — NotifyEvent handler (OCPP 2.0.1).

New in 2.0.1 — chargers report hardware / software events
(component faults, firmware updates, etc.).
"""

from __future__ import annotations

import logging

from ocpp.v201 import call_result

logger = logging.getLogger(__name__)


def handle_notify_event(
    generated_at: str,
    seq_no: int,
    event_data: list,
    **kwargs,
) -> call_result.NotifyEvent:
    """Log the event and acknowledge."""
    logger.info(
        "NotifyEvent  generated_at=%s  seq=%d  events=%d  extras=%s",
        generated_at,
        seq_no,
        len(event_data),
        kwargs,
    )
    return call_result.NotifyEvent()
