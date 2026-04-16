"""core.V20.transaction_event — TransactionEvent handler (OCPP 2.0.1)."""

from __future__ import annotations

import logging

from ocpp.v201 import call_result

from shared.db.client import get_db, db_available
from shared.db.models import ChargingSession
from shared.live_state import (
    apply_energy_to_session,
    extract_energy_wh,
    parse_ocpp_timestamp,
)
from shared.normalizer import normalize_tx_event_v201

logger = logging.getLogger(__name__)


def handle_transaction_event(
    charge_point_id: str = "",
    event_type: str = "",
    timestamp: str = "",
    trigger_reason: str = "",
    seq_no: int = 0,
    transaction_info: dict = None,
    **kwargs,
) -> call_result.TransactionEvent:
    """Process a V201 TransactionEvent."""
    if transaction_info is None:
        transaction_info = {}

    logger.info(
        "TransactionEvent  id=%s  type=%s  trigger=%s  seq=%d  tx=%s  ts=%s  extras=%s",
        charge_point_id,
        event_type,
        trigger_reason,
        seq_no,
        transaction_info,
        timestamp,
        kwargs,
    )

    normalized = normalize_tx_event_v201(
        event_type=event_type,
        timestamp=timestamp,
        trigger_reason=trigger_reason,
        seq_no=seq_no,
        transaction_info=transaction_info,
        **kwargs,
    )

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is None:
                    pass
                elif event_type == "Started":
                    _handle_started(db, charge_point_id, normalized, timestamp)
                elif event_type == "Updated":
                    _handle_updated(db, charge_point_id, normalized)
                elif event_type == "Ended":
                    _handle_ended(db, charge_point_id, normalized, timestamp)
        except Exception:
            logger.exception(
                "Failed to persist TransactionEvent (%s) for %s",
                event_type,
                charge_point_id,
            )

    return call_result.TransactionEvent()


def _handle_started(db, charge_point_id: str, normalized: dict, timestamp: str):
    """Create a new ChargingSession for a Started event."""
    session = (
        db.query(ChargingSession)
        .filter_by(
            charger_id=charge_point_id,
            transaction_id=normalized["transaction_id"],
        )
        .first()
    )
    if session is None:
        session = ChargingSession(
            charger_id=charge_point_id,
            transaction_id=normalized["transaction_id"],
        )
        db.add(session)

    session.id_tag = normalized.get("id_tag") or session.id_tag
    session.connector_id = normalized.get("connector_id", session.connector_id or 1)
    session.evse_id = normalized.get("evse_id", session.evse_id or 1)
    session.start_time = parse_ocpp_timestamp(timestamp)
    apply_energy_to_session(session, extract_energy_wh(normalized.get("meter_value")))


def _handle_updated(db, charge_point_id: str, normalized: dict):
    """Update an existing session with meter data from an Updated event."""
    session = (
        db.query(ChargingSession)
        .filter_by(
            charger_id=charge_point_id,
            transaction_id=normalized["transaction_id"],
        )
        .first()
    )
    if not session:
        logger.warning(
            "TransactionEvent Updated — session not found for tx=%s",
            normalized["transaction_id"],
        )
        return

    apply_energy_to_session(session, extract_energy_wh(normalized.get("meter_value")))


def _handle_ended(db, charge_point_id: str, normalized: dict, timestamp: str):
    """Close an existing session for an Ended event."""
    session = (
        db.query(ChargingSession)
        .filter_by(
            charger_id=charge_point_id,
            transaction_id=normalized["transaction_id"],
        )
        .first()
    )
    if not session:
        logger.warning(
            "TransactionEvent Ended — session not found for tx=%s",
            normalized["transaction_id"],
        )
        return

    apply_energy_to_session(session, extract_energy_wh(normalized.get("meter_value")))
    session.stop_time = parse_ocpp_timestamp(timestamp)
    session.stop_reason = normalized.get("stop_reason")
