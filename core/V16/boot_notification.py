"""core.V16.boot_notification — BootNotification handler (OCPP 1.6J)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v16 import call_result
from ocpp.v16.enums import RegistrationStatus

from shared.constants import HEARTBEAT_INTERVAL_S
from shared.normalizer import normalize_boot_v16
from shared.db.client import get_db, db_available
from shared.db.models import Charger

logger = logging.getLogger(__name__)


def handle_boot_notification(
    charge_point_id: str,
    charge_point_vendor: str,
    charge_point_model: str,
    **kwargs,
) -> call_result.BootNotification:
    """Process a v1.6 BootNotification request."""
    logger.info(
        "BootNotification  id=%s  vendor=%s  model=%s  extras=%s",
        charge_point_id,
        charge_point_vendor,
        charge_point_model,
        kwargs,
    )

    normalized = normalize_boot_v16(
        charge_point_vendor=charge_point_vendor,
        charge_point_model=charge_point_model,
        **kwargs,
    )

    if db_available():
        try:
            with get_db() as db:
                if db is None:
                    pass
                else:
                    charger = db.query(Charger).filter_by(charger_id=charge_point_id).first()
                    if charger:
                        charger.vendor = normalized["vendor"]
                        charger.model = normalized["model"]
                        charger.serial_number = normalized.get("serial_number")
                        charger.firmware_version = normalized.get("firmware_version")
                        charger.ocpp_version = normalized["ocpp_version"]
                        charger.status = "Available"
                        charger.last_heartbeat = datetime.now(tz=timezone.utc)
                    else:
                        charger = Charger(
                            charger_id=charge_point_id,
                            vendor=normalized["vendor"],
                            model=normalized["model"],
                            serial_number=normalized.get("serial_number"),
                            firmware_version=normalized.get("firmware_version"),
                            ocpp_version=normalized["ocpp_version"],
                            status="Available",
                            last_heartbeat=datetime.now(tz=timezone.utc),
                        )
                        db.add(charger)
        except Exception:
            logger.exception("Failed to persist BootNotification for %s", charge_point_id)

    return call_result.BootNotification(
        current_time=datetime.now(tz=timezone.utc).isoformat(),
        interval=HEARTBEAT_INTERVAL_S,
        status=RegistrationStatus.accepted,
    )
