"""core.V16.start_transaction — StartTransaction handler (OCPP 1.6J)."""

from __future__ import annotations

import itertools
import logging

from ocpp.v16 import call_result
from ocpp.v16.enums import AuthorizationStatus

from shared.db.client import get_db, db_available
from shared.db.models import ChargingSession
from shared.live_state import parse_ocpp_timestamp
from shared.normalizer import normalize_start_tx_v16

logger = logging.getLogger(__name__)

# In-memory counter for when DB is not available (echo/debug mode).
_tx_counter = itertools.count(start=1)


def handle_start_transaction(
    charge_point_id: str = "",
    connector_id: int = 1,
    id_tag: str = "",
    meter_start: int = 0,
    timestamp: str = "",
    **kwargs,
) -> call_result.StartTransaction:
    """Accept the transaction, normalize, persist session, return tx_id."""
    normalized = normalize_start_tx_v16(
        connector_id=connector_id,
        id_tag=id_tag,
        meter_start=meter_start,
        timestamp=timestamp,
        **kwargs,
    )

    tx_id = next(_tx_counter)  # Fallback for no-DB mode

    logger.info(
        "StartTransaction  id=%s  connector=%d  id_tag=%s  meter_start=%d  ts=%s",
        charge_point_id,
        connector_id,
        id_tag,
        meter_start,
        timestamp,
    )

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is not None:
                    session = ChargingSession(
                        charger_id=charge_point_id,
                        transaction_id=str(tx_id),  # Temporary placeholder
                        id_tag=normalized["id_tag"],
                        connector_id=normalized["connector_id"],
                        evse_id=normalized["evse_id"],
                        meter_start=normalized["meter_start"],
                        start_time=parse_ocpp_timestamp(timestamp),
                    )
                    db.add(session)
                    db.flush()  # Populate auto-generated session.id

                    # Use the DB-generated session PK as the stable transaction_id.
                    # This survives server restarts, unlike the in-memory counter.
                    session.transaction_id = str(session.id)
                    tx_id = session.id

                    logger.info(
                        "StartTransaction persisted  tx_id=%d  session_pk=%d",
                        tx_id,
                        session.id,
                    )
        except Exception:
            logger.exception(
                "Failed to persist StartTransaction for %s", charge_point_id
            )

    return call_result.StartTransaction(
        transaction_id=tx_id,
        id_tag_info={"status": AuthorizationStatus.accepted},
    )

