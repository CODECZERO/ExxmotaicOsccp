"""
shared — Cross-cutting utilities used by core, api, echo, and echo-n.

Exports constants, the normalizer, the database layer, and the env loader.
"""

from shared.constants import (  # noqa: F401
    OCPP_V16,
    OCPP_V201,
    OCPP_V16_SUBPROTOCOL,
    OCPP_V201_SUBPROTOCOL,
    HEARTBEAT_INTERVAL_S,
    BIND_HOST,
    DATABASE_URL,
    SECRET_KEY,
    API_KEY,
    CORE_PORT,
    API_PORT,
    ECHO_PORT,
    ECHO_N_PORT,
    LOG_LEVEL,
    LOG_FILE,
    CHARGER_DEFAULT_VENDOR,
    CHARGER_DEFAULT_MODEL,
    CHARGER_MODELS,
)
from shared.env import load_env  # noqa: F401
