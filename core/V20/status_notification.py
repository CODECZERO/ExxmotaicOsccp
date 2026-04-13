"""
core.V20.status_notification — StatusNotification handler (OCPP 2.0.1).
"""

from __future__ import annotations

import logging

from ocpp.v201 import call_result

logger = logging.getLogger(__name__)


def handle_status_notification(
    timestamp: str,
    connector_status: str,
    evse_id: int,
    connector_id: int,
    **kwargs,
) -> call_result.StatusNotification:
    """Log status and return an empty confirmation."""
    logger.info(
        "StatusNotification  evse=%d  connector=%d  status=%s  ts=%s  extras=%s",
        evse_id,
        connector_id,
        connector_status,
        timestamp,
        kwargs,
    )
    return call_result.StatusNotification()
