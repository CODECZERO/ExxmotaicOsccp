"""core.V20.meter_values — MeterValues handler (OCPP 2.0.1)."""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from ocpp.v201 import call_result

from shared.db.client import get_db, db_available
from shared.db.models import MeterValue
from shared.live_state import (
    apply_energy_to_session,
    parse_ocpp_timestamp,
    resolve_session_for_meter,
)
from shared.normalizer import normalize_meter_v201

logger = logging.getLogger(__name__)


def handle_meter_values(
    charge_point_id: str = "",
    evse_id: int = 0,
    meter_value: List[Dict[str, Any]] = None,
    **kwargs,
) -> call_result.MeterValues:
    """Log meter samples, normalize, and persist to DB."""
    if meter_value is None:
        meter_value = []

    logger.info(
        "MeterValues  id=%s  evse=%d  samples=%d  extras=%s",
        charge_point_id,
        evse_id,
        len(meter_value),
        kwargs,
    )

    readings = normalize_meter_v201(
        evse_id=evse_id,
        meter_value=meter_value,
        **kwargs,
    )

    if db_available() and charge_point_id and readings:
        try:
            with get_db() as db:
                if db is not None:
                    for reading in readings:
                        session = resolve_session_for_meter(
                            db,
                            charge_point_id,
                            connector_id=reading["connector_id"],
                            evse_id=reading["evse_id"],
                        )
                        apply_energy_to_session(session, reading.get("energy_wh"))

                        mv = MeterValue(
                            charger_id=charge_point_id,
                            connector_id=reading["connector_id"],
                            evse_id=reading["evse_id"],
                            timestamp=parse_ocpp_timestamp(reading.get("timestamp")),
                            energy_wh=reading.get("energy_wh"),
                            power_w=reading.get("power_w"),
                            voltage=reading.get("voltage"),
                            current_a=reading.get("current_a"),
                            soc=reading.get("soc"),
                            raw_json=reading.get("raw_json"),
                            session_id=session.id if session else None,
                        )
                        db.add(mv)
        except Exception:
            logger.exception("Failed to persist MeterValues for %s", charge_point_id)

    return call_result.MeterValues()
