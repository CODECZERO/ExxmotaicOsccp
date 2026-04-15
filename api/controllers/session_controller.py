"""api.controllers.session_controller — Session business logic."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from shared.db.client import get_db, db_available
from shared.db.models import ChargingSession

logger = logging.getLogger(__name__)


def _check_db() -> Tuple[Dict[str, Any], int] | None:
    """Return an error tuple if DB is unavailable, else None."""
    if not db_available():
        return {"error": "Database not configured"}, 503
    return None


def list_all() -> Tuple[Dict[str, Any], int]:
    """Return all sessions from the database."""
    err = _check_db()
    if err:
        return err

    logger.info("Listing all sessions")
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503
            sessions = (
                db.query(ChargingSession)
                .order_by(ChargingSession.created_at.desc())
                .limit(100)
                .all()
            )
            data = [s.to_dict() for s in sessions]
            return {"sessions": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list sessions")
        return {"error": "Failed to retrieve sessions"}, 500


def get_by_id(session_id: str) -> Tuple[Dict[str, Any], int]:
    """Return a single session by primary key or transaction_id."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            # Try by primary key first, then by transaction_id
            session = None
            if session_id.isdigit():
                session = db.query(ChargingSession).filter_by(id=int(session_id)).first()
            if not session:
                session = db.query(ChargingSession).filter_by(transaction_id=session_id).first()

            if not session:
                logger.warning("Session not found: %s", session_id)
                return {"error": f"Session '{session_id}' not found"}, 404
            return {"session": session.to_dict()}, 200
    except Exception:
        logger.exception("Failed to get session %s", session_id)
        return {"error": "Failed to retrieve session"}, 500


def list_by_charger(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Return all sessions for a specific charger."""
    err = _check_db()
    if err:
        return err

    logger.info("Listing sessions for charger %s", charger_id)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503
            sessions = (
                db.query(ChargingSession)
                .filter_by(charger_id=charger_id)
                .order_by(ChargingSession.created_at.desc())
                .all()
            )
            data = [s.to_dict() for s in sessions]
            return {"sessions": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list sessions for charger %s", charger_id)
        return {"error": "Failed to retrieve sessions"}, 500


def list_active() -> Tuple[Dict[str, Any], int]:
    """Return all currently active sessions (stop_time IS NULL)."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503
            sessions = (
                db.query(ChargingSession)
                .filter(ChargingSession.stop_time.is_(None))
                .order_by(ChargingSession.created_at.desc())
                .all()
            )
            data = [s.to_dict() for s in sessions]
            return {"sessions": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list active sessions")
        return {"error": "Failed to retrieve active sessions"}, 500


def stop(session_id: str) -> Tuple[Dict[str, Any], int]:
    """Stop an active session — set stop_time and compute energy consumed."""
    err = _check_db()
    if err:
        return err

    logger.info("Stopping session %s", session_id)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            # Find session by PK or transaction_id
            session = None
            if session_id.isdigit():
                session = db.query(ChargingSession).filter_by(id=int(session_id)).first()
            if not session:
                session = db.query(ChargingSession).filter_by(transaction_id=session_id).first()

            if not session:
                return {"error": f"Session '{session_id}' not found"}, 404

            if session.stop_time is not None:
                return {"error": f"Session '{session_id}' is already stopped"}, 409

            session.stop_time = datetime.now(tz=timezone.utc)
            session.stop_reason = "Remote"

            # Compute energy consumed if meter data is available
            if session.meter_start is not None and session.meter_stop is not None:
                session.energy_kwh = round(
                    (session.meter_stop - session.meter_start) / 1000.0, 3
                )

            return {
                "message": f"Session '{session_id}' stopped",
                "session": session.to_dict(),
            }, 200
    except Exception:
        logger.exception("Failed to stop session %s", session_id)
        return {"error": "Failed to stop session"}, 500
