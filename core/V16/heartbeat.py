"""core.V16.heartbeat — Heartbeat handler (OCPP 1.6J)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v16 import call_result

from shared.db.client import get_db, db_available
from shared.db.models import Charger

logger = logging.getLogger(__name__)


def handle_heartbeat(charge_point_id: str = "", **kwargs) -> call_result.Heartbeat:
    """Return the current server time and update last_heartbeat in DB."""
    logger.debug("Heartbeat received  id=%s  extras=%s", charge_point_id, kwargs)

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is not None:
                    charger = db.query(Charger).filter_by(charger_id=charge_point_id).first()
                    if charger:
                        charger.last_heartbeat = datetime.now(tz=timezone.utc)
        except Exception:
            logger.exception("Failed to update heartbeat for %s", charge_point_id)

    return call_result.Heartbeat(
        current_time=datetime.now(tz=timezone.utc).isoformat(),
    )
