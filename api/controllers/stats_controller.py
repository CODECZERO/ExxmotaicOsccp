"""api.controllers.stats_controller — Dashboard statistics logic."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

from sqlalchemy import func

from shared.db.client import get_db, db_available
from shared.db.models import Charger, ChargingSession, MeterValue, CommandLog

logger = logging.getLogger(__name__)


def _check_db() -> Tuple[Dict[str, Any], int] | None:
    """Return an error tuple if DB is unavailable, else None."""
    if not db_available():
        return {"error": "Database not configured"}, 503
    return None


def get_dashboard() -> Tuple[Dict[str, Any], int]:
    """Return aggregated platform statistics."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            threshold = datetime.now(tz=timezone.utc) - timedelta(minutes=5)
            
            # Dynamic status clause: If heartbeat is stale (>5m), mark as Unavailable
            from sqlalchemy import case
            effective_status = case(
                (Charger.last_heartbeat < threshold, "Unavailable"),
                (Charger.last_heartbeat.is_(None), "Unavailable"),
                else_=Charger.status
            )

            total_chargers = db.query(func.count(Charger.id)).scalar() or 0
            online_chargers = (
                db.query(func.count(Charger.id))
                .filter(effective_status != "Unavailable")
                .scalar() or 0
            )
            chargers_by_status = dict(
                db.query(effective_status, func.count(Charger.id))
                .group_by(effective_status)
                .all()
            )
            chargers_by_version = dict(
                db.query(Charger.ocpp_version, func.count(Charger.id))
                .group_by(Charger.ocpp_version)
                .all()
            )

            total_sessions = db.query(func.count(ChargingSession.id)).scalar() or 0
            active_sessions = (
                db.query(func.count(ChargingSession.id))
                .filter(ChargingSession.stop_time.is_(None))
                .scalar() or 0
            )
            total_energy_kwh = (
                db.query(func.sum(ChargingSession.energy_kwh)).scalar() or 0.0
            )

            total_commands = db.query(func.count(CommandLog.id)).scalar() or 0

            return {
                "stats": {
                    "chargers": {
                        "total": total_chargers,
                        "online": online_chargers,
                        "by_status": chargers_by_status,
                        "by_version": chargers_by_version,
                    },
                    "sessions": {
                        "total": total_sessions,
                        "active": active_sessions,
                        "total_energy_kwh": round(total_energy_kwh, 3),
                    },
                    "commands": {
                        "total": total_commands,
                    },
                },
            }, 200
    except Exception:
        logger.exception("Failed to compute dashboard stats")
        return {"error": "Failed to compute statistics"}, 500


def get_charger_stats(charger_id: str) -> Tuple[Dict[str, Any], int]:
    """Return statistics for a specific charger."""
    err = _check_db()
    if err:
        return err

    try:
        with get_db() as db:
            if db is None:
                return {"error": "Database session unavailable"}, 503

            charger = db.query(Charger).filter_by(charger_id=charger_id).first()
            if not charger:
                return {"error": f"Charger '{charger_id}' not found"}, 404

            total_sessions = (
                db.query(func.count(ChargingSession.id))
                .filter_by(charger_id=charger_id)
                .scalar() or 0
            )
            active_sessions = (
                db.query(func.count(ChargingSession.id))
                .filter_by(charger_id=charger_id)
                .filter(ChargingSession.stop_time.is_(None))
                .scalar() or 0
            )
            total_energy_kwh = (
                db.query(func.sum(ChargingSession.energy_kwh))
                .filter_by(charger_id=charger_id)
                .scalar() or 0.0
            )
            total_meter_readings = (
                db.query(func.count(MeterValue.id))
                .filter_by(charger_id=charger_id)
                .scalar() or 0
            )
            total_commands = (
                db.query(func.count(CommandLog.id))
                .filter_by(charger_id=charger_id)
                .scalar() or 0
            )

            return {
                "charger": charger.to_dict(),
                "stats": {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "total_energy_kwh": round(total_energy_kwh, 3),
                    "total_meter_readings": total_meter_readings,
                    "total_commands": total_commands,
                },
            }, 200
    except Exception:
        logger.exception("Failed to compute stats for charger %s", charger_id)
        return {"error": "Failed to compute charger statistics"}, 500
