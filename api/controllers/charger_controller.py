"""api.controllers.charger_controller — Charger business logic."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from shared.db.client import get_db, db_available
from shared.db.models import Charger
from shared.constants import CHARGER_DEFAULT_VENDOR, CHARGER_DEFAULT_MODEL

logger = logging.getLogger(__name__)


def _check_db() -> Tuple[Dict[str, Any], int] | None:
    """Return an error tuple if DB is unavailable, else None."""
    if not db_available():
        return {"error": "Database not configured"}, 503
    return None


def list_all() -> Tuple[Dict[str, Any], int]:
    """Return all chargers from the database."""
    err = _check_db()
    if err:
        return err

    logger.info("Listing all chargers")
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503
            chargers = db.query(Charger).order_by(Charger.created_at.desc()).all()
            data = [c.to_dict() for c in chargers]
            return {"chargers": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list chargers")
        return {"error": "Failed to retrieve chargers"}, 500


def get_by_id(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Return a single charger by charger_id."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503
            charger = db.query(Charger).filter_by(charger_id=charger_id).first()
            if not charger:
                logger.warning("Charger not found: %s", charger_id)
                return {"error": f"Charger '{charger_id}' not found"}, 404
            return {"charger": charger.to_dict()}, 200
    except Exception:
        logger.exception("Failed to get charger %s", charger_id)
        return {"error": "Failed to retrieve charger"}, 500


def create(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Register a new charger in the database."""
    err = _check_db()
    if err:
        return err

    charger_id = payload.get("charger_id")
    if not charger_id:
        return {"error": "charger_id is required"}, 400

    logger.info("Creating charger with payload: %s", payload)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            existing = db.query(Charger).filter_by(charger_id=charger_id).first()
            if existing:
                return {"error": f"Charger '{charger_id}' already exists"}, 409

            charger = Charger(
                charger_id=charger_id,
                vendor=payload.get("vendor", CHARGER_DEFAULT_VENDOR),
                model=payload.get("model", CHARGER_DEFAULT_MODEL),
                serial_number=payload.get("serial_number"),
                firmware_version=payload.get("firmware_version"),
                ocpp_version=payload.get("ocpp_version", "1.6"),
                status="Available",
                last_heartbeat=datetime.now(tz=timezone.utc),
            )
            db.add(charger)
            db.flush()  # Get the generated id
            return {"charger": charger.to_dict(), "message": "Charger registered"}, 201
    except Exception:
        logger.exception("Failed to create charger")
        return {"error": "Failed to create charger"}, 500


def update(charger_id: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Update an existing charger."""
    err = _check_db()
    if err:
        return err

    logger.info("Updating charger %s with payload: %s", charger_id, payload)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger = db.query(Charger).filter_by(charger_id=charger_id).first()
            if not charger:
                return {"error": f"Charger '{charger_id}' not found"}, 404

            # Update only provided fields
            updatable = ["vendor", "model", "serial_number", "firmware_version", "ocpp_version", "status"]
            for field in updatable:
                if field in payload:
                    setattr(charger, field, payload[field])

            return {"charger": charger.to_dict(), "message": "Charger updated"}, 200
    except Exception:
        logger.exception("Failed to update charger %s", charger_id)
        return {"error": "Failed to update charger"}, 500


def delete(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Delete a charger from the database."""
    err = _check_db()
    if err:
        return err

    logger.info("Deleting charger %s", charger_id)
    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger = db.query(Charger).filter_by(charger_id=charger_id).first()
            if not charger:
                return {"error": f"Charger '{charger_id}' not found"}, 404

            db.delete(charger)
            db.commit()
            return {"message": f"Charger '{charger_id}' deleted"}, 200
    except Exception:
        logger.exception("Failed to delete charger %s", charger_id)
        return {"error": "Failed to delete charger"}, 500
