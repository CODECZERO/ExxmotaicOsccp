"""api.controllers.live_controller — Snapshot helpers for SSE live updates."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, text

from shared.db.client import db_available, get_db
from shared.db.models import Charger, ChargingSession, CommandLog, MeterValue

logger = logging.getLogger(__name__)


def build_snapshot(
    charger_id: str | None = None, session_id: str | None = None
) -> dict[str, Any]:
    """Build a compact snapshot used to detect live-state changes.

    Optimized: uses a SINGLE SQL query to gather all aggregates instead of
    firing 16 separate queries.  This is critical on t2.micro + remote DB.
    """
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

            # ── Build ONE aggregated query ────────────────────────────
            # Instead of 16 separate queries, we do a single round-trip.
            filters = []
            params: dict[str, Any] = {}

            if charger is not None:
                filters.append("c.charger_id = :cid")
                filters.append("s.charger_id = :cid")
                filters.append("m.charger_id = :cid")
                filters.append("cmd.charger_id = :cid")
                params["cid"] = charger.charger_id
            elif charger_id:
                filters.append("c.charger_id = :cid")
                filters.append("s.charger_id = :cid")
                filters.append("m.charger_id = :cid")
                filters.append("cmd.charger_id = :cid")
                params["cid"] = charger_id

            c_where = f"WHERE c.charger_id = :cid" if "cid" in params else ""
            s_where = f"WHERE s.charger_id = :cid" if "cid" in params else ""
            m_where = f"WHERE m.charger_id = :cid" if "cid" in params else ""
            cmd_where = f"WHERE cmd.charger_id = :cid" if "cid" in params else ""

            if session is not None:
                s_extra = f" AND s.id = :sid" if s_where else f"WHERE s.id = :sid"
                s_where += s_extra
                m_extra = f" AND m.session_id = :sid" if m_where else f"WHERE m.session_id = :sid"
                m_where += m_extra
                params["sid"] = session.id

            sql = text(f"""
                SELECT
                    (SELECT MAX(c.updated_at)     FROM chargers c {c_where})  AS max_charger_updated,
                    (SELECT MAX(c.last_heartbeat)  FROM chargers c {c_where})  AS max_heartbeat,
                    (SELECT MAX(s.created_at)      FROM sessions s {s_where}) AS max_session_created,
                    (SELECT MAX(s.start_time)       FROM sessions s {s_where}) AS max_session_start,
                    (SELECT MAX(s.stop_time)        FROM sessions s {s_where}) AS max_session_stop,
                    (SELECT MAX(m.timestamp)        FROM meter_values m {m_where})      AS max_meter_ts,
                    (SELECT MAX(cmd.created_at)     FROM command_logs cmd {cmd_where})  AS max_cmd_created,
                    (SELECT MAX(m.id)               FROM meter_values m {m_where})      AS max_meter_id,
                    (SELECT MAX(cmd.id)             FROM command_logs cmd {cmd_where})  AS max_command_id,
                    (SELECT COUNT(c.id)             FROM chargers c {c_where})          AS charger_count,
                    (SELECT COUNT(s.id)             FROM sessions s {s_where}) AS session_count,
                    (SELECT COUNT(s.id)             FROM sessions s {s_where} {"AND" if s_where else "WHERE"} s.stop_time IS NULL) AS active_session_count,
                    (SELECT COUNT(m.id)             FROM meter_values m {m_where})      AS meter_count,
                    (SELECT COUNT(cmd.id)           FROM command_logs cmd {cmd_where})  AS command_count
            """)

            row = db.execute(sql, params).fetchone()

            latest_activity = _max_timestamp(
                row.max_charger_updated,
                row.max_heartbeat,
                row.max_session_created,
                row.max_session_start,
                row.max_session_stop,
                row.max_meter_ts,
                row.max_cmd_created,
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
                "latest_activity": latest_activity.isoformat()
                if latest_activity
                else None,
                "max_meter_id": row.max_meter_id or 0,
                "max_command_id": row.max_command_id or 0,
                "charger": {
                    "exists": charger is not None,
                    "status": charger.to_dict()["status"] if charger is not None else None,
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
                    "chargers": row.charger_count or 0,
                    "sessions": row.session_count or 0,
                    "active_sessions": row.active_session_count or 0,
                    "meter_values": row.meter_count or 0,
                    "commands": row.command_count or 0,
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
