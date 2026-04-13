"""
core.V20.transaction_event — TransactionEvent handler (OCPP 2.0.1).

Replaces v1.6's StartTransaction / StopTransaction with a unified
event-driven model.
"""

from __future__ import annotations

import logging

from ocpp.v201 import call_result

logger = logging.getLogger(__name__)


def handle_transaction_event(
    event_type: str,
    timestamp: str,
    trigger_reason: str,
    seq_no: int,
    transaction_info: dict,
    **kwargs,
) -> call_result.TransactionEvent:
    """Log the event and return an empty confirmation."""
    logger.info(
        "TransactionEvent  type=%s  trigger=%s  seq=%d  tx=%s  ts=%s  extras=%s",
        event_type,
        trigger_reason,
        seq_no,
        transaction_info,
        timestamp,
        kwargs,
    )
    return call_result.TransactionEvent()
