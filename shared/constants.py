"""shared.constants — Central configuration constants."""

from __future__ import annotations

import os

OCPP_V16: str = "1.6"
OCPP_V201: str = "2.0.1"

OCPP_V16_SUBPROTOCOL: str = "ocpp1.6"
OCPP_V201_SUBPROTOCOL: str = "ocpp2.0.1"

HEARTBEAT_INTERVAL_S: int = int(os.getenv("HEARTBEAT_INTERVAL_S", "10"))

BIND_HOST: str = os.getenv("BIND_HOST", "0.0.0.0")

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@localhost:5432/exxomatic",
)

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
API_KEY: str = os.getenv("API_KEY", "change-me-in-production")

CORE_PORT: int = int(os.getenv("CORE_PORT", "5000"))
API_PORT: int = int(os.getenv("API_PORT", "5050"))
ECHO_PORT: int = int(os.getenv("ECHO_PORT", "8000"))
ECHO_N_PORT: int = int(os.getenv("ECHO_N_PORT", "5001"))

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")

CHARGER_DEFAULT_VENDOR: str = os.getenv("CHARGER_DEFAULT_VENDOR", "TKT")
CHARGER_DEFAULT_MODEL: str = os.getenv("CHARGER_DEFAULT_MODEL", "DC-60kW")

# Real TKT EV charger models for validation / seeding
CHARGER_MODELS: dict = {
    "AC-7kW":   {"power_kw": 7,   "type": "AC", "connector": "Type2",   "voltage": "230V"},
    "AC-11kW":  {"power_kw": 11,  "type": "AC", "connector": "Type2",   "voltage": "400V"},
    "AC-22kW":  {"power_kw": 22,  "type": "AC", "connector": "Type2",   "voltage": "400V"},
    "DC-20kW":  {"power_kw": 20,  "type": "DC", "connector": "CCS2",    "voltage": "150-1000V"},
    "DC-40kW":  {"power_kw": 40,  "type": "DC", "connector": "CCS2",    "voltage": "150-1000V"},
    "DC-60kW":  {"power_kw": 60,  "type": "DC", "connector": "CCS2",    "voltage": "150-1000V"},
    "DC-80kW":  {"power_kw": 80,  "type": "DC", "connector": "CCS2",    "voltage": "150-1000V"},
    "DC-120kW": {"power_kw": 120, "type": "DC", "connector": "CCS2/CHAdeMO", "voltage": "150-1000V"},
    "DC-160kW": {"power_kw": 160, "type": "DC", "connector": "CCS2/CHAdeMO", "voltage": "150-1000V"},
    "DC-180kW": {"power_kw": 180, "type": "DC", "connector": "CCS2/CHAdeMO", "voltage": "150-1000V"},
    "DC-240kW": {"power_kw": 240, "type": "DC", "connector": "CCS2/CHAdeMO", "voltage": "150-1000V"},
}
