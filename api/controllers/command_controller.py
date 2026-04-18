"""api.controllers.command_controller — Remote charger command logic."""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from shared.db.client import get_db, db_available
from shared.db.models import Charger, CommandLog

logger = logging.getLogger(__name__)


def _check_db() -> Tuple[Dict[str, Any], int] | None:
    """Return an error tuple if DB is unavailable, else None."""
    if not db_available():
        return {"error": "Database not configured"}, 503
    return None


def _get_charger(db, charger_id: str):
    """Look up a charger by charger_id, return (charger, error_tuple)."""
    charger = db.query(Charger).filter_by(charger_id=charger_id).first()
    if not charger:
        return None, ({"error": f"Charger '{charger_id}' not found"}, 404)
    return charger, None


def _log_command(db, charger_id: str, command: str, payload: dict, ocpp_version: str = None):
    """Insert a row in the command_logs table."""
    log_entry = CommandLog(
        charger_id=charger_id,
        command=command,
        payload=payload,
        status="Pending",
        ocpp_version=ocpp_version,
    )
    db.add(log_entry)
    return log_entry


def list_command_logs(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Return all command logs for a charger."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger, charger_err = _get_charger(db, charger_id)
            if charger_err:
                return charger_err

            logs = (
                db.query(CommandLog)
                .filter_by(charger_id=charger_id)
                .order_by(CommandLog.created_at.desc())
                .all()
            )
            data = [log.to_dict() for log in logs]
            return {"command_logs": data, "count": len(data)}, 200
    except Exception:
        logger.exception("Failed to list command logs for %s", charger_id)
        return {"error": "Failed to retrieve command logs"}, 500


def remote_start(charger_id: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Send RemoteStartTransaction to charger."""
    err = _check_db()
    if err:
        return err

    id_tag = payload.get("id_tag", "UNKNOWN")
    connector_id = payload.get("connector_id", 1)
    logger.info("RemoteStart  charger=%s  id_tag=%s  connector=%d", charger_id, id_tag, connector_id)

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger, charger_err = _get_charger(db, charger_id)
            if charger_err:
                return charger_err

            log_entry = _log_command(
                db, charger_id, "RemoteStartTransaction",
                {"id_tag": id_tag, "connector_id": connector_id},
                charger.ocpp_version,
            )

            return {
                "message": f"RemoteStart sent to '{charger_id}'",
                "charger_id": charger_id,
                "id_tag": id_tag,
                "connector_id": connector_id,
                "ocpp_version": charger.ocpp_version,
                "status": "Accepted",
                "command_log_id": log_entry.id if log_entry.id else None,
            }, 200
    except Exception:
        logger.exception("Failed to process RemoteStart for %s", charger_id)
        return {"error": "Failed to process command"}, 500


def remote_stop(charger_id: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Send RemoteStopTransaction to charger."""
    err = _check_db()
    if err:
        return err

    tx_id = payload.get("transaction_id")
    logger.info("RemoteStop  charger=%s  tx_id=%s", charger_id, tx_id)

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger, charger_err = _get_charger(db, charger_id)
            if charger_err:
                return charger_err

            _log_command(
                db, charger_id, "RemoteStopTransaction",
                {"transaction_id": tx_id},
                charger.ocpp_version,
            )

            return {
                "message": f"RemoteStop sent to '{charger_id}'",
                "charger_id": charger_id,
                "transaction_id": tx_id,
                "ocpp_version": charger.ocpp_version,
                "status": "Accepted",
            }, 200
    except Exception:
        logger.exception("Failed to process RemoteStop for %s", charger_id)
        return {"error": "Failed to process command"}, 500


def reset(charger_id: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Send Reset to charger."""
    err = _check_db()
    if err:
        return err

    reset_type = payload.get("type", "Soft")
    logger.info("Reset  charger=%s  type=%s", charger_id, reset_type)

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger, charger_err = _get_charger(db, charger_id)
            if charger_err:
                return charger_err

            _log_command(
                db, charger_id, "Reset",
                {"type": reset_type},
                charger.ocpp_version,
            )

            return {
                "message": f"Reset ({reset_type}) sent to '{charger_id}'",
                "charger_id": charger_id,
                "type": reset_type,
                "ocpp_version": charger.ocpp_version,
                "status": "Accepted",
            }, 200
    except Exception:
        logger.exception("Failed to process Reset for %s", charger_id)
        return {"error": "Failed to process command"}, 500


def unlock(charger_id: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Send UnlockConnector to charger."""
    err = _check_db()
    if err:
        return err

    connector_id = payload.get("connector_id", 1)
    logger.info("Unlock  charger=%s  connector=%d", charger_id, connector_id)

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger, charger_err = _get_charger(db, charger_id)
            if charger_err:
                return charger_err

            _log_command(
                db, charger_id, "UnlockConnector",
                {"connector_id": connector_id},
                charger.ocpp_version,
            )

            return {
                "message": f"Unlock sent to '{charger_id}' connector {connector_id}",
                "charger_id": charger_id,
                "connector_id": connector_id,
                "ocpp_version": charger.ocpp_version,
                "status": "Unlocked",
            }, 200
    except Exception:
        logger.exception("Failed to process Unlock for %s", charger_id)
        return {"error": "Failed to process command"}, 500
