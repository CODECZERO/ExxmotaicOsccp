"""core.router — version detection and ChargePoint factory."""

from __future__ import annotations

import logging
from typing import List

import websockets

from core.V16 import V16ChargePoint
from core.V20 import V201ChargePoint
from shared.constants import (
    OCPP_V16,
    OCPP_V201,
    OCPP_V16_SUBPROTOCOL,
    OCPP_V201_SUBPROTOCOL,
)

logger = logging.getLogger(__name__)


def detect_version(path: str) -> str:
    """Extract the OCPP version from a WebSocket request path."""
    normalised = path.strip("/").lower()

    if OCPP_V201 in normalised:
        return OCPP_V201
    if OCPP_V16 in normalised:
        return OCPP_V16

    logger.warning("Could not detect OCPP version from path '%s', defaulting to %s", path, OCPP_V16)
    return OCPP_V16


def get_subprotocols() -> List[str]:
    """Return the list of OCPP sub-protocols the server advertises."""
    return [OCPP_V16_SUBPROTOCOL, OCPP_V201_SUBPROTOCOL]


def create_charge_point(
    charge_point_id: str,
    connection: websockets.WebSocketServerProtocol,
    version: str,
):
    """
    Factory — return the correct ChargePoint subclass for *version*.
    """
    if version == OCPP_V201:
        logger.info("Creating V201ChargePoint for %s", charge_point_id)
        return V201ChargePoint(charge_point_id, connection)

    logger.info("Creating V16ChargePoint for %s", charge_point_id)
    return V16ChargePoint(charge_point_id, connection)
