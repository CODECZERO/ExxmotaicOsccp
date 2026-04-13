"""
core.V20.heartbeat — Heartbeat handler (OCPP 2.0.1).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v201 import call_result

logger = logging.getLogger(__name__)


def handle_heartbeat(**kwargs) -> call_result.Heartbeat:
    """Return the current server time."""
    logger.debug("Heartbeat received  extras=%s", kwargs)
    return call_result.Heartbeat(
        current_time=datetime.now(tz=timezone.utc).isoformat(),
    )
