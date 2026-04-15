"""core.V20.status_notification — StatusNotification handler (OCPP 2.0.1)."""

from __future__ import annotations

import logging

from ocpp.v201 import call_result

from shared.normalizer import normalize_status_v201
from shared.db.client import get_db, db_available
from shared.db.models import Charger

logger = logging.getLogger(__name__)


def handle_status_notification(
    charge_point_id: str = "",
    timestamp: str = "",
    connector_status: str = "",
    evse_id: int = 0,
    connector_id: int = 0,
    **kwargs,
) -> call_result.StatusNotification:
    """Log the status change, normalize, and update charger in DB."""
    logger.info(
        "StatusNotification  id=%s  evse=%d  connector=%d  status=%s  ts=%s  extras=%s",
        charge_point_id,
        evse_id,
        connector_id,
        connector_status,
        timestamp,
        kwargs,
    )

    normalized = normalize_status_v201(
        timestamp=timestamp,
        connector_status=connector_status,
        evse_id=evse_id,
        connector_id=connector_id,
        **kwargs,
    )

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is not None:
                    charger = db.query(Charger).filter_by(charger_id=charge_point_id).first()
                    if charger:
                        charger.status = normalized["status"]
                        charger.error_code = normalized.get("error_code")
        except Exception:
            logger.exception("Failed to update status for %s", charge_point_id)

    return call_result.StatusNotification()
