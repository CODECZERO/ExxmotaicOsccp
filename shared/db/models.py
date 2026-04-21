"""shared.db.models — SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Charger(Base):
    """A registered charge point."""

    __tablename__ = "chargers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    charger_id = Column(String(64), unique=True, nullable=False, index=True)
    vendor = Column(String(128), nullable=False, default="")
    model = Column(String(128), nullable=False, default="")
    serial_number = Column(String(128), nullable=True)
    firmware_version = Column(String(64), nullable=True)
    ocpp_version = Column(String(8), nullable=False, default="1.6")
    status = Column(String(32), nullable=False, default="Available")
    error_code = Column(String(64), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    sessions = relationship("ChargingSession", back_populates="charger", lazy="dynamic", cascade="all, delete-orphan")
    meter_values = relationship("MeterValue", back_populates="charger", lazy="dynamic", cascade="all, delete-orphan")
    command_logs = relationship("CommandLog", back_populates="charger", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for API responses using dynamic status."""
        effective_status = self.status
        now = datetime.now(tz=timezone.utc)
        hb = self.last_heartbeat
        if hb is not None and hb.tzinfo is None:
            hb = hb.replace(tzinfo=timezone.utc)
        if not hb or (now - hb).total_seconds() > 300:
            effective_status = "Unavailable"

        return {
            "id": self.id,
            "charger_id": self.charger_id,
            "vendor": self.vendor,
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "ocpp_version": self.ocpp_version,
            "status": effective_status,
            "error_code": self.error_code,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChargingSession(Base):
    """A charging session (transaction)."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    charger_id = Column(
        String(64),
        ForeignKey("chargers.charger_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id = Column(String(64), nullable=False, index=True)
    id_tag = Column(String(64), nullable=True)
    connector_id = Column(Integer, nullable=False, default=1)
    evse_id = Column(Integer, nullable=False, default=1)
    meter_start = Column(Integer, nullable=True)
    meter_stop = Column(Integer, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    stop_time = Column(DateTime(timezone=True), nullable=True)
    stop_reason = Column(String(32), nullable=True)
    energy_kwh = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    charger = relationship("Charger", back_populates="sessions", foreign_keys=[charger_id],
                           primaryjoin="ChargingSession.charger_id == Charger.charger_id")
    meter_values = relationship("MeterValue", back_populates="session", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for API responses."""
        return {
            "id": self.id,
            "charger_id": self.charger_id,
            "transaction_id": self.transaction_id,
            "id_tag": self.id_tag,
            "connector_id": self.connector_id,
            "evse_id": self.evse_id,
            "meter_start": self.meter_start,
            "meter_stop": self.meter_stop,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "stop_reason": self.stop_reason,
            "energy_kwh": self.energy_kwh,
            "active": self.stop_time is None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MeterValue(Base):
    """A single meter reading snapshot."""

    __tablename__ = "meter_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    charger_id = Column(
        String(64),
        ForeignKey("chargers.charger_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_id = Column(Integer, nullable=False, default=1)
    evse_id = Column(Integer, nullable=False, default=1)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    energy_wh = Column(Float, nullable=True)
    power_w = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    current_a = Column(Float, nullable=True)
    soc = Column(Float, nullable=True)
    raw_json = Column(JSON, nullable=True)

    # Relationships
    charger = relationship("Charger", back_populates="meter_values", foreign_keys=[charger_id],
                           primaryjoin="MeterValue.charger_id == Charger.charger_id")
    session = relationship("ChargingSession", back_populates="meter_values", foreign_keys=[session_id],
                           primaryjoin="MeterValue.session_id == ChargingSession.id")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for API responses."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "charger_id": self.charger_id,
            "connector_id": self.connector_id,
            "evse_id": self.evse_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "energy_wh": self.energy_wh,
            "power_w": self.power_w,
            "voltage": self.voltage,
            "current_a": self.current_a,
            "soc": self.soc,
        }


class CommandLog(Base):
    """Audit trail for remote commands sent to chargers."""

    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    charger_id = Column(
        String(64),
        ForeignKey("chargers.charger_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    command = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(255), nullable=False, default="Pending")
    ocpp_version = Column(String(8), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    charger = relationship("Charger", back_populates="command_logs", foreign_keys=[charger_id],
                           primaryjoin="CommandLog.charger_id == Charger.charger_id")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for API responses."""
        return {
            "id": self.id,
            "charger_id": self.charger_id,
            "command": self.command,
            "payload": self.payload,
            "status": self.status,
            "ocpp_version": self.ocpp_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
