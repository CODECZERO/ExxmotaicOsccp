"""core.V16.status_notification — StatusNotification handler (OCPP 1.6J)."""

from __future__ import annotations

import logging

from ocpp.v16 import call_result

from shared.normalizer import normalize_status_v16
from shared.db.client import get_db, db_available
from shared.db.models import Charger

logger = logging.getLogger(__name__)


def handle_status_notification(
    charge_point_id: str = "",
    connector_id: int = 0,
    error_code: str = "",
    status: str = "",
    **kwargs,
) -> call_result.StatusNotification:
    """Log the status change, normalize, and update charger in DB."""
    logger.info(
        "StatusNotification  id=%s  connector=%d  status=%s  error=%s  extras=%s",
        charge_point_id,
        connector_id,
        status,
        error_code,
        kwargs,
    )

    normalized = normalize_status_v16(
        connector_id=connector_id,
        error_code=error_code,
        status=status,
        **kwargs,
    )

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is not None:
                    charger = db.query(Charger).filter_by(charger_id=charge_point_id).first()
                    if charger:
                        charger.status = normalized["status"]
                        charger.error_code = normalized["error_code"]
        except Exception:
            logger.exception("Failed to update status for %s", charge_point_id)

    return call_result.StatusNotification()
