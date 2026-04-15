"""core.V20.transaction_event — TransactionEvent handler (OCPP 2.0.1)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v201 import call_result

from shared.normalizer import normalize_tx_event_v201
from shared.db.client import get_db, db_available
from shared.db.models import ChargingSession

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
    parse_ts = _parse_timestamp(timestamp)

    session = ChargingSession(
        charger_id=charge_point_id,
        transaction_id=normalized["transaction_id"],
        id_tag=normalized.get("id_tag", ""),
        connector_id=normalized.get("connector_id", 1),
        evse_id=normalized.get("evse_id", 1),
        meter_start=0,
        start_time=parse_ts,
    )
    db.add(session)


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

    # Extract latest energy from meter_value if present
    meter_value = normalized.get("meter_value")
    if meter_value and isinstance(meter_value, list):
        for mv in meter_value:
            sampled = mv.get("sampled_value", [])
            for sample in sampled:
                value_str = str(sample.get("value", ""))
                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    continue
                measurand = sample.get("measurand", "")
                if not measurand or "energy" in measurand.lower():
                    session.meter_stop = int(value)


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

    parse_ts = _parse_timestamp(timestamp)
    session.stop_time = parse_ts
    session.stop_reason = normalized.get("stop_reason")

    # Compute energy consumed
    if session.meter_start is not None and session.meter_stop is not None:
        session.energy_kwh = round(
            (session.meter_stop - session.meter_start) / 1000.0, 3
        )


def _parse_timestamp(timestamp: str):
    """Parse an ISO timestamp string, falling back to UTC now."""
    if timestamp:
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            pass
    return datetime.now(tz=timezone.utc)
