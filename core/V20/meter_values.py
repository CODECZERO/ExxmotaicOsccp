"""
core.V20.meter_values — MeterValues handler (OCPP 2.0.1).
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from ocpp.v201 import call_result

logger = logging.getLogger(__name__)


def handle_meter_values(
    evse_id: int,
    meter_value: List[Dict[str, Any]],
    **kwargs,
) -> call_result.MeterValues:
    """Log meter samples and return an empty confirmation."""
    logger.info(
        "MeterValues  evse=%d  samples=%d  extras=%s",
        evse_id,
        len(meter_value),
        kwargs,
    )
    return call_result.MeterValues()
