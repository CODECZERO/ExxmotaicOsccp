"""Helpers for persisting live OCPP state into the database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from shared.db.models import ChargingSession


def parse_ocpp_timestamp(timestamp: str | datetime | None) -> datetime:
    """Parse charger timestamps, falling back to UTC now."""
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp

    if timestamp:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass

    return datetime.now(tz=timezone.utc)


def extract_energy_wh(meter_values: list[dict[str, Any]] | None) -> int | None:
    """Extract the latest cumulative imported energy reading from OCPP samples."""
    latest_energy: float | None = None

    for meter_value in meter_values or []:
        for sample in meter_value.get("sampled_value", []):
            measurand = str(sample.get("measurand", "")).lower()
            if measurand and "energy" not in measurand:
                continue

            try:
                latest_energy = float(str(sample.get("value", "")))
            except (TypeError, ValueError):
                continue

    if latest_energy is None:
        return None

    return int(latest_energy)


def find_session_by_transaction(
    db: Session,
    charger_id: str,
    transaction_id: str | int | None,
) -> ChargingSession | None:
    """Return a session matching the transaction id for a charger."""
    if transaction_id in (None, ""):
        return None

    return (
        db.query(ChargingSession)
        .filter_by(charger_id=charger_id, transaction_id=str(transaction_id))
        .first()
    )


def find_active_session(
    db: Session,
    charger_id: str,
    connector_id: int | None = None,
    evse_id: int | None = None,
) -> ChargingSession | None:
    """Return the newest active session for a charger, preferring connector/EVSE matches."""
    query = db.query(ChargingSession).filter_by(charger_id=charger_id)
    query = query.filter(ChargingSession.stop_time.is_(None))

    if evse_id not in (None, 0):
        query = query.filter_by(evse_id=evse_id)
    if connector_id not in (None, 0):
        query = query.filter_by(connector_id=connector_id)

    session = query.order_by(ChargingSession.id.desc()).first()
    if session is not None:
        return session

    return (
        db.query(ChargingSession)
        .filter_by(charger_id=charger_id)
        .filter(ChargingSession.stop_time.is_(None))
        .order_by(ChargingSession.id.desc())
        .first()
    )


def resolve_session_for_meter(
    db: Session,
    charger_id: str,
    transaction_id: str | int | None = None,
    connector_id: int | None = None,
    evse_id: int | None = None,
) -> ChargingSession | None:
    """Resolve a meter reading to a transaction or active session."""
    session = find_session_by_transaction(db, charger_id, transaction_id)
    if session is not None:
        return session

    return find_active_session(
        db,
        charger_id,
        connector_id=connector_id,
        evse_id=evse_id,
    )


def apply_energy_to_session(
    session: ChargingSession | None, energy_wh: int | None
) -> None:
    """Update a session with the latest cumulative energy reading."""
    if session is None or energy_wh is None:
        return

    if session.meter_start in (None, 0):
        session.meter_start = energy_wh

    session.meter_stop = energy_wh

    if session.meter_stop >= session.meter_start:
        session.energy_kwh = round(
            (session.meter_stop - session.meter_start) / 1000.0,
            3,
        )
