"""
core.V16.boot_notification — BootNotification handler (OCPP 1.6J).

Called when a charger first connects and announces its vendor / model.
Returns Accepted so the charger knows it is registered.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v16 import call_result
from ocpp.v16.enums import RegistrationStatus

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_S = 10


def handle_boot_notification(
    charge_point_vendor: str,
    charge_point_model: str,
    **kwargs,
) -> call_result.BootNotification:
    """
    Process a v1.6 BootNotification request.

    Always accepts — this is the echo / debug behaviour.
    Production code would look up an allow-list in the DB.
    """
    logger.info(
        "BootNotification  vendor=%s  model=%s  extras=%s",
        charge_point_vendor,
        charge_point_model,
        kwargs,
    )

    return call_result.BootNotification(
        current_time=datetime.now(tz=timezone.utc).isoformat(),
        interval=HEARTBEAT_INTERVAL_S,
        status=RegistrationStatus.accepted,
    )
