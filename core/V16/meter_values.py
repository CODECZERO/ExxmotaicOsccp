"""
core.V16.meter_values — MeterValues handler (OCPP 1.6J).

Chargers periodically report energy/power/voltage/current readings.
Echo server logs and ACKs.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from ocpp.v16 import call_result

logger = logging.getLogger(__name__)


def handle_meter_values(
    connector_id: int,
    meter_value: List[Dict[str, Any]],
    **kwargs,
) -> call_result.MeterValues:
    """Log the meter samples and return an empty confirmation."""
    logger.info(
        "MeterValues  connector=%d  samples=%d  extras=%s",
        connector_id,
        len(meter_value),
        kwargs,
    )
    return call_result.MeterValues()
