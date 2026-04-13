"""
core.V16.start_transaction — StartTransaction handler (OCPP 1.6J).

Called when a charger begins a charging session.  Echo server always
accepts and hands back a monotonically increasing transaction_id.
"""

from __future__ import annotations

import itertools
import logging

from ocpp.v16 import call_result
from ocpp.v16.enums import AuthorizationStatus

logger = logging.getLogger(__name__)

# Simple in-memory counter — fine for echo / debug.
_tx_counter = itertools.count(start=1)


def handle_start_transaction(
    connector_id: int,
    id_tag: str,
    meter_start: int,
    timestamp: str,
    **kwargs,
) -> call_result.StartTransaction:
    """Accept the transaction and issue a sequential transaction id."""
    tx_id = next(_tx_counter)
    logger.info(
        "StartTransaction  connector=%d  id_tag=%s  meter_start=%d  ts=%s  tx_id=%d",
        connector_id,
        id_tag,
        meter_start,
        timestamp,
        tx_id,
    )
    return call_result.StartTransaction(
        transaction_id=tx_id,
        id_tag_info={"status": AuthorizationStatus.accepted},
    )
