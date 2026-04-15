"""core.V20.boot_notification — BootNotification handler (OCPP 2.0.1)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v201 import call_result
from ocpp.v201.enums import RegistrationStatusEnumType

from shared.constants import HEARTBEAT_INTERVAL_S
from shared.normalizer import normalize_boot_v201
from shared.db.client import get_db, db_available
from shared.db.models import Charger

logger = logging.getLogger(__name__)


def handle_boot_notification(
    charge_point_id: str = "",
    charging_station: dict = None,
    reason: str = "",
    **kwargs,
) -> call_result.BootNotification:
    """Process a v2.0.1 BootNotification request."""
    if charging_station is None:
        charging_station = {}

    logger.info(
        "BootNotification  id=%s  station=%s  reason=%s  extras=%s",
        charge_point_id,
        charging_station,
        reason,
        kwargs,
    )

    normalized = normalize_boot_v201(
        charging_station=charging_station,
        reason=reason,
        **kwargs,
    )

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is not None:
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
        status=RegistrationStatusEnumType.accepted,
    )
