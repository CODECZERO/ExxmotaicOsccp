"""
core.V16.heartbeat — Heartbeat handler (OCPP 1.6J).

Chargers send periodic heartbeats to signal they are still online.
We reply with the server's current UTC timestamp.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v16 import call_result

logger = logging.getLogger(__name__)


def handle_heartbeat(**kwargs) -> call_result.Heartbeat:
    """Return the current server time."""
    logger.debug("Heartbeat received  extras=%s", kwargs)
    return call_result.Heartbeat(
        current_time=datetime.now(tz=timezone.utc).isoformat(),
    )
