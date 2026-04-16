"""api.controllers.live_controller — Snapshot helpers for SSE live updates."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

from shared.db.client import db_available, get_db
from shared.db.models import Charger, ChargingSession, CommandLog, MeterValue

logger = logging.getLogger(__name__)


def build_snapshot(
    charger_id: str | None = None, session_id: str | None = None
) -> dict[str, Any]:
    """Build a compact snapshot used to detect live-state changes."""
    scope = {
        "charger_id": charger_id,
        "session_id": session_id,
    }

    if not db_available():
        snapshot = {
            "scope": scope,
            "db_available": False,
            "updated_at": _utc_now().isoformat(),
        }
        snapshot["signature"] = _sign_snapshot(snapshot)
        return snapshot

    try:
        with get_db() as db:
            if db is None:
                snapshot = {
                    "scope": scope,
                    "db_available": False,
                    "updated_at": _utc_now().isoformat(),
                }
                snapshot["signature"] = _sign_snapshot(snapshot)
                return snapshot

            charger = _get_charger(db, charger_id)
            session = _get_session(db, session_id)

            session_query = db.query(ChargingSession)
            meter_query = db.query(MeterValue)
            command_query = db.query(CommandLog)
            charger_query = db.query(Charger)

            if charger is not None:
                session_query = session_query.filter_by(charger_id=charger.charger_id)
                meter_query = meter_query.filter_by(charger_id=charger.charger_id)
                command_query = command_query.filter_by(charger_id=charger.charger_id)
                charger_query = charger_query.filter_by(charger_id=charger.charger_id)
            elif charger_id:
                charger_query = charger_query.filter_by(charger_id=charger_id)
                session_query = session_query.filter_by(charger_id=charger_id)
                meter_query = meter_query.filter_by(charger_id=charger_id)
                command_query = command_query.filter_by(charger_id=charger_id)

            if session is not None:
                session_query = session_query.filter_by(id=session.id)
                meter_query = meter_query.filter_by(session_id=session.id)
            elif session_id:
                # Keep the requested scope in the signature even if the session is absent.
                session_query = session_query.filter(ChargingSession.id == -1)
                meter_query = meter_query.filter(MeterValue.id == -1)

            latest_activity = _max_timestamp(
                charger_query.with_entities(func.max(Charger.updated_at)).scalar(),
                charger_query.with_entities(func.max(Charger.last_heartbeat)).scalar(),
                session_query.with_entities(
                    func.max(ChargingSession.created_at)
                ).scalar(),
                session_query.with_entities(
                    func.max(ChargingSession.start_time)
                ).scalar(),
                session_query.with_entities(
                    func.max(ChargingSession.stop_time)
                ).scalar(),
                meter_query.with_entities(func.max(MeterValue.timestamp)).scalar(),
                command_query.with_entities(func.max(CommandLog.created_at)).scalar(),
            )

            snapshot = {
                "scope": {
                    "charger_id": charger.charger_id
                    if charger is not None
                    else charger_id,
                    "session_id": str(session.id)
                    if session is not None
                    else session_id,
                },
                "db_available": True,
                "charger": {
                    "exists": charger is not None,
                    "status": charger.status if charger is not None else None,
                    "last_heartbeat": charger.last_heartbeat.isoformat()
                    if charger and charger.last_heartbeat
                    else None,
                },
                "session": {
                    "exists": session is not None,
                    "active": session.stop_time is None
                    if session is not None
                    else None,
                    "charger_id": session.charger_id if session is not None else None,
                },
                "counts": {
                    "chargers": charger_query.with_entities(
                        func.count(Charger.id)
                    ).scalar()
                    or 0,
                    "sessions": session_query.with_entities(
                        func.count(ChargingSession.id)
                    ).scalar()
                    or 0,
                    "active_sessions": session_query.filter(
                        ChargingSession.stop_time.is_(None)
                    )
                    .with_entities(func.count(ChargingSession.id))
                    .scalar()
                    or 0,
                    "meter_values": meter_query.with_entities(
                        func.count(MeterValue.id)
                    ).scalar()
                    or 0,
                    "commands": command_query.with_entities(
                        func.count(CommandLog.id)
                    ).scalar()
                    or 0,
                },
                "updated_at": latest_activity.isoformat()
                if latest_activity
                else _utc_now().isoformat(),
            }
            snapshot["signature"] = _sign_snapshot(snapshot)
            return snapshot
    except Exception:
        logger.exception("Failed to build live snapshot")
        snapshot = {
            "scope": scope,
            "db_available": False,
            "error": "snapshot_unavailable",
            "updated_at": _utc_now().isoformat(),
        }
        snapshot["signature"] = _sign_snapshot(snapshot)
        return snapshot


def _get_charger(db, charger_id: str | None) -> Charger | None:
    if not charger_id:
        return None
    return db.query(Charger).filter_by(charger_id=charger_id).first()


def _get_session(db, session_id: str | None) -> ChargingSession | None:
    if not session_id:
        return None

    session = None
    if session_id.isdigit():
        session = db.query(ChargingSession).filter_by(id=int(session_id)).first()
    if session is None:
        session = db.query(ChargingSession).filter_by(transaction_id=session_id).first()
    return session


def _sign_snapshot(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _max_timestamp(*values: datetime | None) -> datetime | None:
    valid = [value for value in values if value is not None]
    return max(valid) if valid else None


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)
