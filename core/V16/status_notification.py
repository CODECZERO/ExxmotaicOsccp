"""
core.V16.status_notification — StatusNotification handler (OCPP 1.6J).

Chargers report connector status changes here (Available, Charging,
Faulted, etc.).  Echo server just logs and ACKs.
"""

from __future__ import annotations

import logging

from ocpp.v16 import call_result

logger = logging.getLogger(__name__)


def handle_status_notification(
    connector_id: int,
    error_code: str,
    status: str,
    **kwargs,
) -> call_result.StatusNotification:
    """Log the status change and return an empty confirmation."""
    logger.info(
        "StatusNotification  connector=%d  status=%s  error=%s  extras=%s",
        connector_id,
        status,
        error_code,
        kwargs,
    )
    return call_result.StatusNotification()
