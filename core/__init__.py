"""
core — OCPP WebSocket handler library.

Exports version-specific ChargePoint classes and the router utilities
that echo / echo-n / the production server all share.
"""

from core.V16 import V16ChargePoint          # noqa: F401
from core.V20 import V201ChargePoint         # noqa: F401
from core.router import (                    # noqa: F401
    detect_version,
    get_subprotocols,
    create_charge_point,
)
