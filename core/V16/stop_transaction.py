"""core.V16.stop_transaction — StopTransaction handler (OCPP 1.6J)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ocpp.v16 import call_result

from shared.normalizer import normalize_stop_tx_v16
from shared.db.client import get_db, db_available
from shared.db.models import ChargingSession

logger = logging.getLogger(__name__)


def handle_stop_transaction(
    charge_point_id: str = "",
    meter_stop: int = 0,
    timestamp: str = "",
    transaction_id: int = 0,
    **kwargs,
) -> call_result.StopTransaction:
    """Acknowledge the stopped transaction, normalize, and update session in DB."""
    normalized = normalize_stop_tx_v16(
        meter_stop=meter_stop,
        timestamp=timestamp,
        transaction_id=transaction_id,
        **kwargs,
    )

    logger.info(
        "StopTransaction  id=%s  tx_id=%d  meter_stop=%d  ts=%s  extras=%s",
        charge_point_id,
        transaction_id,
        meter_stop,
        timestamp,
        kwargs,
    )

    if db_available() and charge_point_id:
        try:
            with get_db() as db:
                if db is not None:
                    session = (
                        db.query(ChargingSession)
                        .filter_by(
                            charger_id=charge_point_id,
                            transaction_id=normalized["transaction_id"],
                        )
                        .first()
                    )
                    if session:
                        parse_ts = None
                        if timestamp:
                            try:
                                parse_ts = datetime.fromisoformat(timestamp)
                            except ValueError:
                                parse_ts = datetime.now(tz=timezone.utc)

                        session.meter_stop = normalized["meter_stop"]
                        session.stop_time = parse_ts
                        session.stop_reason = normalized.get("stop_reason")

                        # Compute energy consumed
                        if session.meter_start is not None and session.meter_stop is not None:
                            session.energy_kwh = round(
                                (session.meter_stop - session.meter_start) / 1000.0, 3
                            )
        except Exception:
            logger.exception("Failed to persist StopTransaction for %s", charge_point_id)

    return call_result.StopTransaction()
