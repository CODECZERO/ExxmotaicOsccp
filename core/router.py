"""
core.router — version detection and ChargePoint factory.

Parses the WebSocket request path to decide whether the connecting
charger speaks OCPP 1.6J or 2.0.1, then returns the right handler.
"""

from __future__ import annotations

import logging
from typing import List

import websockets

from core.V16 import V16ChargePoint
from core.V20 import V201ChargePoint

logger = logging.getLogger(__name__)


def detect_version(path: str) -> str:
    """
    Extract the OCPP version from a WebSocket request path.

    Expected formats:
        /ocpp/1.6/<charger_id>   → "1.6"
        /ocpp/2.0.1/<charger_id> → "2.0.1"

    Falls back to "1.6" when the path doesn't match any known pattern
    (most Indian chargers run 1.6J).
    """
    normalised = path.strip("/").lower()

    if "2.0.1" in normalised:
        return "2.0.1"
    if "1.6" in normalised:
        return "1.6"

    logger.warning("Could not detect OCPP version from path '%s', defaulting to 1.6", path)
    return "1.6"


def get_subprotocols() -> List[str]:
    """Return the list of OCPP sub-protocols the server advertises."""
    return ["ocpp1.6", "ocpp2.0.1"]


def create_charge_point(
    charge_point_id: str,
    connection: websockets.WebSocketServerProtocol,
    version: str,
):
    """
    Factory — return the correct ChargePoint subclass for *version*.
    """
    if version == "2.0.1":
        logger.info("Creating V201ChargePoint for %s", charge_point_id)
        return V201ChargePoint(charge_point_id, connection)

    logger.info("Creating V16ChargePoint for %s", charge_point_id)
    return V16ChargePoint(charge_point_id, connection)
