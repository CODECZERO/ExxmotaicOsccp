"""
core.V20.boot_notification — BootNotification handler (OCPP 2.0.1).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v201 import call_result
from ocpp.v201.enums import RegistrationStatusEnumType

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_S = 10


def handle_boot_notification(
    charging_station: dict,
    reason: str,
    **kwargs,
) -> call_result.BootNotification:
    """
    Process a v2.0.1 BootNotification.

    ``charging_station`` is a dict with keys like vendorName, model,
    serialNumber, etc.
    """
    logger.info(
        "BootNotification  station=%s  reason=%s  extras=%s",
        charging_station,
        reason,
        kwargs,
    )
    return call_result.BootNotification(
        current_time=datetime.now(tz=timezone.utc).isoformat(),
        interval=HEARTBEAT_INTERVAL_S,
        status=RegistrationStatusEnumType.accepted,
    )
