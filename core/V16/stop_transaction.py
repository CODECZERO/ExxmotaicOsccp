"""
core.V16.stop_transaction — StopTransaction handler (OCPP 1.6J).

Called when a charger ends a charging session.
"""

from __future__ import annotations

import logging

from ocpp.v16 import call_result

logger = logging.getLogger(__name__)


def handle_stop_transaction(
    meter_stop: int,
    timestamp: str,
    transaction_id: int,
    **kwargs,
) -> call_result.StopTransaction:
    """Acknowledge the stopped transaction."""
    logger.info(
        "StopTransaction  tx_id=%d  meter_stop=%d  ts=%s  extras=%s",
        transaction_id,
        meter_stop,
        timestamp,
        kwargs,
    )
    return call_result.StopTransaction()
