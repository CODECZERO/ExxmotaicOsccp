-- =====================================================================
-- Exxomatic OCPP — Database Migration 001: Initial Schema
--
-- Creates the three core tables: chargers, sessions, meter_values.
-- Run with:  psql $DATABASE_URL -f shared/db/migrations/001_init.sql
-- =====================================================================

BEGIN;

-- ─── Chargers ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chargers (
    id              SERIAL PRIMARY KEY,
    charger_id      VARCHAR(64)  NOT NULL UNIQUE,
    vendor          VARCHAR(128) NOT NULL DEFAULT '',
    model           VARCHAR(128) NOT NULL DEFAULT '',
    serial_number   VARCHAR(128),
    firmware_version VARCHAR(64),
    ocpp_version    VARCHAR(8)   NOT NULL DEFAULT '1.6',
    status          VARCHAR(32)  NOT NULL DEFAULT 'Available',
    error_code      VARCHAR(64),
    last_heartbeat  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chargers_charger_id ON chargers (charger_id);
CREATE INDEX IF NOT EXISTS idx_chargers_status ON chargers (status);

-- ─── Sessions (Charging Transactions) ───────────────────────────────

CREATE TABLE IF NOT EXISTS sessions (
    id              SERIAL PRIMARY KEY,
    charger_id      VARCHAR(64)  NOT NULL,
    transaction_id  VARCHAR(64)  NOT NULL,
    id_tag          VARCHAR(64),
    connector_id    INTEGER      NOT NULL DEFAULT 1,
    evse_id         INTEGER      NOT NULL DEFAULT 1,
    meter_start     INTEGER,
    meter_stop      INTEGER,
    start_time      TIMESTAMPTZ,
    stop_time       TIMESTAMPTZ,
    stop_reason     VARCHAR(32),
    energy_kwh      DOUBLE PRECISION,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_charger_id ON sessions (charger_id);
CREATE INDEX IF NOT EXISTS idx_sessions_transaction_id ON sessions (transaction_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions (stop_time) WHERE stop_time IS NULL;

-- ─── Meter Values ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS meter_values (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER,
    charger_id      VARCHAR(64)  NOT NULL,
    connector_id    INTEGER      NOT NULL DEFAULT 1,
    evse_id         INTEGER      NOT NULL DEFAULT 1,
    timestamp       TIMESTAMPTZ  NOT NULL,
    energy_wh       DOUBLE PRECISION,
    power_w         DOUBLE PRECISION,
    voltage         DOUBLE PRECISION,
    current_a       DOUBLE PRECISION,
    soc             DOUBLE PRECISION,
    raw_json        JSONB
);

CREATE INDEX IF NOT EXISTS idx_meter_values_charger_id ON meter_values (charger_id);
CREATE INDEX IF NOT EXISTS idx_meter_values_session_id ON meter_values (session_id);
CREATE INDEX IF NOT EXISTS idx_meter_values_timestamp ON meter_values (timestamp);

-- ─── Updated-at trigger ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chargers_updated_at ON chargers;
CREATE TRIGGER trg_chargers_updated_at
    BEFORE UPDATE ON chargers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
