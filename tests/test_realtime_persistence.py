"""Tests for live OCPP persistence into the database."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.V16 import meter_values as v16_meter_values
from core.V16 import start_transaction as v16_start_transaction
from core.V16 import stop_transaction as v16_stop_transaction
from core.V20 import meter_values as v20_meter_values
from core.V20 import transaction_event as v20_transaction_event
from shared.db.models import Base, Charger, ChargingSession, MeterValue


def _install_test_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    @contextmanager
    def mock_get_db():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    for module in (
        v16_start_transaction,
        v16_stop_transaction,
        v16_meter_values,
        v20_transaction_event,
        v20_meter_values,
    ):
        monkeypatch.setattr(module, "db_available", lambda: True)
        monkeypatch.setattr(module, "get_db", mock_get_db)

    return SessionLocal


def test_v16_live_events_persist_into_session(monkeypatch):
    """V16 start, meter, and stop events should update the same session."""
    SessionLocal = _install_test_db(monkeypatch)

    with SessionLocal() as session:
        session.add(Charger(charger_id="TEST_V16", vendor="TKT", model="DC-60kW"))
        session.commit()

    start_response = v16_start_transaction.handle_start_transaction(
        charge_point_id="TEST_V16",
        connector_id=1,
        id_tag="USER-1",
        meter_start=1200,
        timestamp="2026-04-16T08:00:00+00:00",
    )

    v16_meter_values.handle_meter_values(
        charge_point_id="TEST_V16",
        connector_id=1,
        transaction_id=start_response.transaction_id,
        meter_value=[
            {
                "timestamp": "2026-04-16T08:05:00+00:00",
                "sampled_value": [
                    {"value": "3450", "measurand": "Energy.Active.Import.Register"},
                    {"value": "7000", "measurand": "Power.Active.Import"},
                ],
            }
        ],
    )

    v16_stop_transaction.handle_stop_transaction(
        charge_point_id="TEST_V16",
        transaction_id=start_response.transaction_id,
        meter_stop=4200,
        timestamp="2026-04-16T08:10:00+00:00",
        reason="EVDisconnected",
    )

    with SessionLocal() as session:
        persisted = (
            session.query(ChargingSession).filter_by(charger_id="TEST_V16").one()
        )
        reading = session.query(MeterValue).filter_by(charger_id="TEST_V16").one()

        assert persisted.transaction_id == str(start_response.transaction_id)
        assert persisted.meter_start == 1200
        assert persisted.meter_stop == 4200
        assert persisted.energy_kwh == 3.0
        assert reading.session_id == persisted.id
        assert reading.energy_wh == 3450


def test_v201_live_events_attach_meter_values_to_active_session(monkeypatch):
    """V201 transaction and meter events should share a single active session."""
    SessionLocal = _install_test_db(monkeypatch)

    with SessionLocal() as session:
        session.add(Charger(charger_id="TEST_V201", vendor="TKT", model="DC-120kW"))
        session.commit()

    v20_transaction_event.handle_transaction_event(
        charge_point_id="TEST_V201",
        event_type="Started",
        timestamp="2026-04-16T09:00:00+00:00",
        trigger_reason="CablePluggedIn",
        seq_no=1,
        transaction_info={"transaction_id": "TX-201-1"},
        evse={"id": 1, "connector_id": 1},
        id_token={"id_token": "USER-201"},
        meter_value=[
            {
                "timestamp": "2026-04-16T09:00:00+00:00",
                "sampled_value": [
                    {"value": "2000", "measurand": "Energy.Active.Import.Register"}
                ],
            }
        ],
    )

    v20_meter_values.handle_meter_values(
        charge_point_id="TEST_V201",
        evse_id=1,
        meter_value=[
            {
                "timestamp": "2026-04-16T09:05:00+00:00",
                "sampled_value": [
                    {"value": "2600", "measurand": "Energy.Active.Import.Register"},
                    {"value": "9000", "measurand": "Power.Active.Import"},
                ],
            }
        ],
    )

    v20_transaction_event.handle_transaction_event(
        charge_point_id="TEST_V201",
        event_type="Ended",
        timestamp="2026-04-16T09:10:00+00:00",
        trigger_reason="EVCommunicationLost",
        seq_no=2,
        transaction_info={
            "transaction_id": "TX-201-1",
            "stopped_reason": "EVDisconnected",
        },
        meter_value=[
            {
                "timestamp": "2026-04-16T09:10:00+00:00",
                "sampled_value": [
                    {"value": "3200", "measurand": "Energy.Active.Import.Register"}
                ],
            }
        ],
    )

    with SessionLocal() as session:
        persisted = (
            session.query(ChargingSession).filter_by(charger_id="TEST_V201").one()
        )
        reading = session.query(MeterValue).filter_by(charger_id="TEST_V201").one()

        assert persisted.transaction_id == "TX-201-1"
        assert persisted.id_tag == "USER-201"
        assert persisted.meter_start == 2000
        assert persisted.meter_stop == 3200
        assert persisted.energy_kwh == 1.2
        assert persisted.stop_reason == "EVDisconnected"
        assert reading.session_id == persisted.id
        assert reading.energy_wh == 2600
