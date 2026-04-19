"""Seed demo chargers, sessions, meter values, and command logs."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.env import load_env

load_env()

from shared.db.client import engine, get_db
from shared.db.models import Base, Charger, ChargingSession, MeterValue, CommandLog


def upsert_charger(db, payload: dict) -> Charger:
    charger = db.query(Charger).filter_by(charger_id=payload["charger_id"]).first()
    if charger is None:
        charger = Charger(**payload)
        db.add(charger)
        db.flush()
        return charger

    for key, value in payload.items():
        setattr(charger, key, value)
    db.flush()
    return charger


def upsert_session(db, payload: dict) -> ChargingSession:
    session = (
        db.query(ChargingSession)
        .filter_by(transaction_id=payload["transaction_id"])
        .first()
    )
    if session is None:
        session = ChargingSession(**payload)
        db.add(session)
        db.flush()
        return session

    for key, value in payload.items():
        setattr(session, key, value)
    db.flush()
    return session


def replace_meter_values(db, session: ChargingSession, readings: list[dict]) -> None:
    db.query(MeterValue).filter_by(session_id=session.id).delete(
        synchronize_session=False
    )
    for reading in readings:
        db.add(
            MeterValue(session_id=session.id, charger_id=session.charger_id, **reading)
        )
    db.flush()


def replace_command_logs(db, charger_id: str, logs: list[dict]) -> None:
    db.query(CommandLog).filter_by(charger_id=charger_id).delete(
        synchronize_session=False
    )
    for payload in logs:
        db.add(CommandLog(charger_id=charger_id, **payload))
    db.flush()


def main() -> None:
    if engine is None:
        raise SystemExit("DATABASE_URL is not configured.")

    Base.metadata.create_all(bind=engine)

    now = datetime.now(timezone.utc)

    chargers = [
        {
            "charger_id": "DEMO-DC-001",
            "vendor": "TKT",
            "model": "DC-60kW",
            "serial_number": "TKT-DC60-001",
            "firmware_version": "v2.4.1",
            "ocpp_version": "1.6",
            "status": "Charging",
            "error_code": None,
            "last_heartbeat": now - timedelta(minutes=1),
        },
        {
            "charger_id": "DEMO-AC-011",
            "vendor": "TKT",
            "model": "AC-11kW",
            "serial_number": "TKT-AC11-011",
            "firmware_version": "v1.9.3",
            "ocpp_version": "2.0.1",
            "status": "Available",
            "error_code": None,
            "last_heartbeat": now - timedelta(minutes=3),
        },
        {
            "charger_id": "DEMO-DC-120",
            "vendor": "TKT",
            "model": "DC-120kW",
            "serial_number": "TKT-DC120-120",
            "firmware_version": "v3.1.0",
            "ocpp_version": "2.0.1",
            "status": "Faulted",
            "error_code": "ConnectorLockFailure",
            "last_heartbeat": now - timedelta(minutes=14),
        },
    ]

    session_specs = [
        {
            "charger_id": "DEMO-DC-001",
            "transaction_id": "TXN-DEMO-1001",
            "id_tag": "USER-ALPHA",
            "connector_id": 1,
            "evse_id": 1,
            "meter_start": 182340,
            "meter_stop": None,
            "start_time": now - timedelta(minutes=48),
            "stop_time": None,
            "stop_reason": None,
            "energy_kwh": 18.42,
        },
        {
            "charger_id": "DEMO-DC-001",
            "transaction_id": "TXN-DEMO-0998",
            "id_tag": "USER-BETA",
            "connector_id": 1,
            "evse_id": 1,
            "meter_start": 176900,
            "meter_stop": 182100,
            "start_time": now - timedelta(hours=5, minutes=10),
            "stop_time": now - timedelta(hours=4, minutes=22),
            "stop_reason": "EVDisconnected",
            "energy_kwh": 5.2,
        },
        {
            "charger_id": "DEMO-AC-011",
            "transaction_id": "TXN-DEMO-0770",
            "id_tag": "USER-GAMMA",
            "connector_id": 2,
            "evse_id": 1,
            "meter_start": 65420,
            "meter_stop": 68860,
            "start_time": now - timedelta(days=1, hours=2),
            "stop_time": now - timedelta(days=1, hours=1, minutes=18),
            "stop_reason": "Remote",
            "energy_kwh": 3.44,
        },
        {
            "charger_id": "DEMO-DC-120",
            "transaction_id": "TXN-DEMO-0660",
            "id_tag": "FLEET-009",
            "connector_id": 1,
            "evse_id": 1,
            "meter_start": 401100,
            "meter_stop": 410700,
            "start_time": now - timedelta(days=2, hours=3),
            "stop_time": now - timedelta(days=2, hours=2, minutes=5),
            "stop_reason": "Faulted",
            "energy_kwh": 9.6,
        },
    ]

    meter_specs = {
        "TXN-DEMO-1001": [
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(minutes=20),
                "energy_wh": 194500,
                "power_w": 40120,
                "voltage": 399.6,
                "current_a": 100.4,
                "soc": 46.0,
                "raw_json": None,
            },
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(minutes=10),
                "energy_wh": 198900,
                "power_w": 42210,
                "voltage": 401.2,
                "current_a": 105.0,
                "soc": 54.0,
                "raw_json": None,
            },
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(minutes=2),
                "energy_wh": 200760,
                "power_w": 43880,
                "voltage": 403.1,
                "current_a": 108.8,
                "soc": 61.0,
                "raw_json": None,
            },
        ],
        "TXN-DEMO-0998": [
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(hours=5),
                "energy_wh": 177600,
                "power_w": 35500,
                "voltage": 397.0,
                "current_a": 89.4,
                "soc": 33.0,
                "raw_json": None,
            },
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(hours=4, minutes=37),
                "energy_wh": 181200,
                "power_w": 31200,
                "voltage": 395.5,
                "current_a": 78.9,
                "soc": 47.0,
                "raw_json": None,
            },
        ],
        "TXN-DEMO-0770": [
            {
                "connector_id": 2,
                "evse_id": 1,
                "timestamp": now - timedelta(days=1, hours=1, minutes=50),
                "energy_wh": 67010,
                "power_w": 10020,
                "voltage": 230.2,
                "current_a": 43.5,
                "soc": 71.0,
                "raw_json": None,
            },
            {
                "connector_id": 2,
                "evse_id": 1,
                "timestamp": now - timedelta(days=1, hours=1, minutes=25),
                "energy_wh": 68860,
                "power_w": 8940,
                "voltage": 229.1,
                "current_a": 39.0,
                "soc": 82.0,
                "raw_json": None,
            },
        ],
        "TXN-DEMO-0660": [
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(days=2, hours=2, minutes=40),
                "energy_wh": 406000,
                "power_w": 78200,
                "voltage": 735.0,
                "current_a": 106.4,
                "soc": 58.0,
                "raw_json": None,
            },
            {
                "connector_id": 1,
                "evse_id": 1,
                "timestamp": now - timedelta(days=2, hours=2, minutes=10),
                "energy_wh": 410700,
                "power_w": 0,
                "voltage": 0,
                "current_a": 0,
                "soc": 74.0,
                "raw_json": None,
            },
        ],
    }

    command_specs = {
        "DEMO-DC-001": [
            {
                "command": "RemoteStartTransaction",
                "payload": {"id_tag": "USER-ALPHA", "connector_id": 1},
                "status": "Accepted",
                "ocpp_version": "1.6",
                "created_at": now - timedelta(minutes=49),
            },
            {
                "command": "UnlockConnector",
                "payload": {"connector_id": 1},
                "status": "Unlocked",
                "ocpp_version": "1.6",
                "created_at": now - timedelta(hours=3),
            },
        ],
        "DEMO-AC-011": [
            {
                "command": "Reset",
                "payload": {"type": "Soft"},
                "status": "Accepted",
                "ocpp_version": "2.0.1",
                "created_at": now - timedelta(days=1, hours=3),
            },
        ],
        "DEMO-DC-120": [
            {
                "command": "RemoteStopTransaction",
                "payload": {"transaction_id": "TXN-DEMO-0660"},
                "status": "Accepted",
                "ocpp_version": "2.0.1",
                "created_at": now - timedelta(days=2, hours=2),
            },
            {
                "command": "Reset",
                "payload": {"type": "Hard"},
                "status": "Accepted",
                "ocpp_version": "2.0.1",
                "created_at": now - timedelta(minutes=35),
            },
        ],
    }

    with get_db() as db:
        if db is None:
            raise SystemExit("Database session unavailable.")

        for charger_payload in chargers:
            upsert_charger(db, charger_payload)

        created_sessions: dict[str, ChargingSession] = {}
        for session_payload in session_specs:
            created_sessions[session_payload["transaction_id"]] = upsert_session(
                db, session_payload
            )

        for transaction_id, readings in meter_specs.items():
            replace_meter_values(db, created_sessions[transaction_id], readings)

        for charger_id, logs in command_specs.items():
            replace_command_logs(db, charger_id, logs)

    print("Demo data seeded successfully.")
    print("Chargers: DEMO-DC-001, DEMO-AC-011, DEMO-DC-120")


if __name__ == "__main__":
    main()
