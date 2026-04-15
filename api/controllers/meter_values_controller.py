"""api.controllers.meter_values_controller — Meter value query logic."""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from shared.db.client import get_db, db_available
from shared.db.models import MeterValue

logger = logging.getLogger(__name__)


def _check_db() -> Tuple[Dict[str, Any], int] | None:
    """Return an error tuple if DB is unavailable, else None."""
    if not db_available():
        return {"error": "Database not configured"}, 503
    return None


def list_by_charger(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Return meter values for a specific charger, newest first."""
    err = _check_db()
    if err:
        return err

    logger.info("Listing meter values for charger %s", charger_id)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            readings = (
                db.query(MeterValue)
                .filter_by(charger_id=charger_id)
                .order_by(MeterValue.timestamp.desc())
                .limit(100)
                .all()
            )
            data = [r.to_dict() for r in readings]
            return {"meter_values": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list meter values for charger %s", charger_id)
        return {"error": "Failed to retrieve meter values"}, 500


def list_by_session(session_id: str) -> Tuple[Dict[str, Any], int]:
    """Return meter values for a specific session."""
    err = _check_db()
    if err:
        return err

    logger.info("Listing meter values for session %s", session_id)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            # Filter by session_id (int PK)
            filter_id = int(session_id) if session_id.isdigit() else None
            if filter_id is None:
                return {"error": "Invalid session_id — must be numeric"}, 400

            readings = (
                db.query(MeterValue)
                .filter_by(session_id=filter_id)
                .order_by(MeterValue.timestamp.desc())
                .all()
            )
            data = [r.to_dict() for r in readings]
            return {"meter_values": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list meter values for session %s", session_id)
        return {"error": "Failed to retrieve meter values"}, 500


def get_latest(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Return the most recent meter reading for a charger."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            reading = (
                db.query(MeterValue)
                .filter_by(charger_id=charger_id)
                .order_by(MeterValue.timestamp.desc())
                .first()
            )
            if not reading:
                return {"error": f"No meter values found for charger '{charger_id}'"}, 404
            return {"meter_value": reading.to_dict()}, 200
    except Exception:
        logger.exception("Failed to get latest meter value for %s", charger_id)
        return {"error": "Failed to retrieve meter value"}, 500
