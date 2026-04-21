# Exxomatic OCPP Platform — Architecture & Deep Scan Report

> **Version:** 1.0 · **Date:** 2026-04-21 · **Scope:** Full codebase deep scan

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Component Deep Dive](#4-component-deep-dive)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [Deployment Architecture](#8-deployment-architecture)
9. [Deep Scan — Issues Found & Fixed](#9-deep-scan--issues-found--fixed)
10. [Technology Stack](#10-technology-stack)

---

## 1. System Overview

Exxomatic is a **production-grade EV charger management platform** implementing the **OCPP (Open Charge Point Protocol)** standard. It supports dual-version protocol handling for both **OCPP 1.6J** and **OCPP 2.0.1**, providing:

- Real-time WebSocket communication with physical EV chargers
- RESTful API for charger management and monitoring
- Live dashboard with Server-Sent Events (SSE)
- Remote command dispatch (Start/Stop/Reset/Unlock)
- Session and meter telemetry persistence
- Dynamic charger health monitoring via heartbeat staleness detection

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INTERNET / CLOUDFLARE                        │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ :80
                ┌─────────▼──────────┐
                │     HAProxy        │
                │  (Reverse Proxy)   │
                │  hostname + path   │
                │     routing        │
                └──┬──┬──┬──┬───────┘
                   │  │  │  │
        ┌──────────┘  │  │  └──────────────┐
        │             │  │                 │
        ▼             ▼  ▼                 ▼
  ┌──────────┐  ┌─────────────┐    ┌──────────────┐
  │ Next.js  │  │  Flask API  │    │  OCPP Core   │
  │ Frontend │  │  (Gunicorn) │    │  WebSocket   │
  │  :3000   │  │   :5050     │    │   :5000      │
  └──────────┘  └──────┬──────┘    └──────┬───────┘
                       │                  │
                       ▼                  ▼
              ┌────────────────┐  ┌───────────────┐
              │  PostgreSQL    │  │  Echo  :8000   │
              │  (shared DB)   │  │  Echo-N :5001  │
              └────────────────┘  │  (debug WS)    │
                                  └───────────────┘
```

### Request Routing (HAProxy)

| Pattern | Backend | Purpose |
|---------|---------|---------|
| `/api/*` or `charger-api.exxomatic.in` | Flask API `:5050` | REST API |
| `/api/live/stream` | Flask API (SSE) | Long-lived SSE stream |
| `/ocpp/*` (WebSocket) | Core `:5000` | Production chargers |
| `/ocpp-echo/*` (WebSocket) | Echo `:8000` | Debug server 1 |
| `/ocpp-echo-n/*` (WebSocket) | Echo-N `:5001` | Debug server 2 |
| Everything else | Next.js `:3000` | Dashboard UI |

---

## 3. Directory Structure

```
exxmotaicOSCCP/
├── api/                          # Flask REST API
│   ├── __init__.py               #   App factory (create_app)
│   ├── main.py                   #   Dev entry point
│   ├── decorators.py             #   Error handler decorator
│   ├── routes/                   #   Blueprint route definitions
│   │   ├── chargers.py           #     CRUD for chargers
│   │   ├── commands.py           #     Remote command endpoints
│   │   ├── sessions.py           #     Session query endpoints
│   │   ├── stats.py              #     Dashboard statistics
│   │   ├── live.py               #     SSE live stream + snapshot
│   │   ├── meter_values.py       #     Meter value queries
│   │   └── health.py             #     Health check
│   └── controllers/              #   Business logic layer
│       ├── charger_controller.py
│       ├── command_controller.py
│       ├── session_controller.py
│       ├── stats_controller.py
│       ├── live_controller.py
│       └── meter_values_controller.py
│
├── core/                         # OCPP WebSocket Server (Production)
│   ├── __init__.py               #   Exports ChargePoint classes
│   ├── main.py                   #   Production WS entry point
│   ├── router.py                 #   Version detection + factory
│   ├── dispatcher.py             #   Command polling + dispatch
│   ├── V16/                      #   OCPP 1.6J handlers
│   │   ├── charge_point.py       #     V16ChargePoint class
│   │   ├── boot_notification.py
│   │   ├── heartbeat.py
│   │   ├── authorize.py
│   │   ├── start_transaction.py
│   │   ├── stop_transaction.py
│   │   ├── status_notification.py
│   │   └── meter_values.py
│   └── V20/                      #   OCPP 2.0.1 handlers
│       ├── charge_point.py       #     V201ChargePoint class
│       ├── boot_notification.py
│       ├── heartbeat.py
│       ├── transaction_event.py
│       ├── status_notification.py
│       ├── meter_values.py
│       └── notify_event.py
│
├── shared/                       # Cross-cutting shared library
│   ├── constants.py              #   All config constants (from env)
│   ├── env.py                    #   .env file loader
│   ├── normalizer.py             #   Version-aware data normalization
│   ├── live_state.py             #   Session resolution + energy calc
│   └── db/                       #   Database layer
│       ├── client.py             #     Engine + session factory
│       ├── models.py             #     SQLAlchemy ORM models
│       └── migrations/
│           └── 001_init.sql
│
├── echo/                         # Debug Echo Server 1 (:8000)
│   ├── main.py                   #   Entry point
│   ├── V16/server.py             #   V16-only factory
│   └── V20/server.py             #   V201-only factory
│
├── echo-n/                       # Debug Echo Server 2 (:5001)
│   ├── main.py                   #   Entry point
│   ├── V16/server.py             #   V16-only factory
│   └── V20/server.py             #   V201-only factory
│
├── web-client/                   # Next.js Dashboard Frontend
│   └── src/
│       ├── app/                  #   Pages (dashboard, sessions, sites)
│       ├── components/           #   UI components
│       ├── hooks/                #   useData, useLiveStream
│       └── lib/                  #   API client, types, formatters
│
├── server/                       # Production deployment config
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── gunicorn.conf.py
│
├── haproxy/
│   └── haproxy.cfg               # Reverse proxy configuration
│
├── tests/                        # Test suite
│   ├── conftest.py               #   Shared fixtures (V16/V201 clients)
│   ├── test_v16_handlers.py
│   ├── test_v201_handlers.py
│   ├── test_api.py
│   ├── test_boot_notification.py
│   ├── test_deletion.py
│   ├── test_echo_boot.py
│   ├── test_local.py
│   ├── test_realtime_persistence.py
│   └── test_remote_servers.py
│
├── scripts/
│   ├── init_db.py                # DB table creation
│   ├── migrate.py                # HTML→TSX converter (legacy)
│   └── generate_css.py
│
├── docker-compose.yml            # Multi-service orchestration
├── requirements.txt              # Python dependencies
├── run_local_stack.sh            # Local dev runner
└── .env.example                  # Environment template
```

---

## 4. Component Deep Dive

### 4.1 OCPP Core — WebSocket Server

The core server accepts WebSocket connections from physical EV chargers and routes them to version-specific handlers.

```
Charger connects via WebSocket
        │
        ▼
  ┌─────────────┐     ┌──────────────┐
  │  core/main  │────▶│  router.py   │
  │  on_connect │     │  detect_ver  │
  └─────────────┘     └──────┬───────┘
                             │
               ┌─────────────┼─────────────┐
               ▼                           ▼
     ┌─────────────────┐       ┌─────────────────────┐
     │  V16ChargePoint  │       │  V201ChargePoint     │
     │  @on handlers:   │       │  @on handlers:       │
     │  · BootNotif     │       │  · BootNotification  │
     │  · Heartbeat     │       │  · Heartbeat         │
     │  · StatusNotif   │       │  · StatusNotification│
     │  · StartTx       │       │  · TransactionEvent  │
     │  · StopTx        │       │  · MeterValues       │
     │  · MeterValues   │       │  · NotifyEvent       │
     │  · Authorize     │       │                      │
     └─────────┬───────┘       └──────────┬───────────┘
               │                          │
               ▼                          ▼
     ┌────────────────────────────────────────────┐
     │         shared/normalizer.py                │
     │  normalize_boot_v16() / normalize_boot_v201 │
     │  normalize_meter_v16() / normalize_meter_v201│
     │  normalize_tx_event_v201() ...               │
     └────────────────────┬───────────────────────┘
                          ▼
     ┌────────────────────────────────────────────┐
     │           shared/db (PostgreSQL)            │
     │  Charger | ChargingSession | MeterValue     │
     └────────────────────────────────────────────┘
```

**Version Detection Logic:** Path-based detection scans the URL for `2.0.1` or `1.6`, defaulting to V16.

**Handler Delegation Pattern:** Each `@on(Action.xxx)` method uses `asyncio.to_thread()` to run synchronous DB-persisting handlers off the event loop, preventing I/O blocking.

### 4.2 Command Dispatcher

The dispatcher runs as a background `asyncio` task polling the DB every 1 second:

```
  ┌──────────────────────────────────────────────┐
  │            CommandPoller Loop (1s)            │
  │                                              │
  │  1. Expire stale commands (TTL=30s)          │
  │  2. Query Pending commands for active CPs    │
  │  3. Dispatch FIFO via ChargePoint.call()     │
  │  4. Per-command timeout (10s)                │
  │  5. Update status → Accepted/Rejected/Error  │
  └──────────────────────────────────────────────┘
```

### 4.3 REST API Layer

**Pattern:** Routes → Controllers → DB (3-tier clean architecture)

- **Routes** (`api/routes/`): Thin Flask Blueprints, HTTP concerns only
- **Controllers** (`api/controllers/`): Business logic, DB queries, validation
- **Decorators** (`api/decorators.py`): Global error handling wrapper

### 4.4 Live Dashboard (SSE)

```
  Browser ──GET /api/live/stream──▶ Flask SSE Generator
                                         │
                                    ┌────▼────┐
                                    │ Snapshot │──▶ SHA1 signature
                                    │ Builder  │
                                    └────┬────┘
                                         │ every 0.5s
                                    ┌────▼────────────┐
                                    │ If signature     │
                                    │ changed → emit   │
                                    │ "update" event   │
                                    │                  │
                                    │ If 15s idle →    │
                                    │ emit "ping"      │
                                    └─────────────────┘
```

### 4.5 Dynamic Health Monitoring

Charger status is **computed at read-time**, not stored:

```
  if last_heartbeat is NULL or older than 5 minutes:
      effective_status = "Unavailable"
  else:
      effective_status = stored database status
```

This pattern eliminates the need for background cron jobs to reap dead connections.

---

## 5. Data Flow Diagrams

### 5.1 Charger Boot → Full Session Lifecycle

```
  ┌──────────┐                    ┌──────────────┐              ┌────────┐
  │  Charger  │                    │  OCPP Server  │              │  DB    │
  └─────┬────┘                    └──────┬───────┘              └───┬────┘
        │                                │                          │
        │──BootNotification─────────────▶│                          │
        │                                │──Upsert Charger─────────▶│
        │◀───────────Accepted────────────│                          │
        │                                │                          │
        │──Heartbeat (every 10s)────────▶│                          │
        │                                │──Update last_heartbeat──▶│
        │◀───────────CurrentTime─────────│                          │
        │                                │                          │
        │──StatusNotification───────────▶│                          │
        │  (Available/Charging/etc.)     │──Update charger.status──▶│
        │◀───────────ACK────────────────│                          │
        │                                │                          │
        │──StartTransaction─────────────▶│                          │
        │  (id_tag, connector, meter)    │──Create Session──────────▶│
        │◀───────────tx_id + Accepted───│                          │
        │                                │                          │
        │──MeterValues──────────────────▶│                          │
        │  (energy, power, voltage, soc) │──Persist + link session─▶│
        │◀───────────ACK────────────────│                          │
        │                                │                          │
        │──StopTransaction──────────────▶│                          │
        │  (meter_stop, reason)          │──Close Session + calc───▶│
        │◀───────────ACK────────────────│     energy_kwh           │
        │                                │                          │
```

### 5.2 Remote Command Flow (API → Charger)

```
  ┌──────────┐         ┌───────────┐        ┌────────────┐       ┌──────────┐
  │ Dashboard │         │  Flask API │        │  Dispatcher │       │  Charger  │
  └─────┬────┘         └─────┬─────┘        └──────┬─────┘       └─────┬────┘
        │                     │                     │                    │
        │──POST /start───────▶│                     │                    │
        │                     │──Insert CommandLog──▶│                    │
        │                     │   status="Pending"   │                    │
        │◀──200 Accepted─────│                     │                    │
        │                     │                     │                    │
        │                     │              ┌──────▼──────┐             │
        │                     │              │ Poll Loop   │             │
        │                     │              │ finds cmd   │             │
        │                     │              └──────┬──────┘             │
        │                     │                     │                    │
        │                     │                     │──call(Request)────▶│
        │                     │                     │◀──Response────────│
        │                     │                     │                    │
        │                     │              ┌──────▼──────┐             │
        │                     │              │ Update cmd  │             │
        │                     │              │ → Accepted  │             │
        │                     │              └─────────────┘             │
```

---

## 6. Database Schema

```
┌─────────────────────────────────────────────────┐
│                   chargers                       │
├─────────────────────────────────────────────────┤
│ id             INTEGER  PK AUTO                  │
│ charger_id     VARCHAR(64)  UNIQUE NOT NULL       │
│ vendor         VARCHAR(128) NOT NULL              │
│ model          VARCHAR(128) NOT NULL              │
│ serial_number  VARCHAR(128) NULLABLE              │
│ firmware_ver   VARCHAR(64)  NULLABLE              │
│ ocpp_version   VARCHAR(8)   NOT NULL  "1.6"       │
│ status         VARCHAR(32)  NOT NULL  "Available"  │
│ error_code     VARCHAR(64)  NULLABLE              │
│ last_heartbeat TIMESTAMP(TZ) NULLABLE             │
│ created_at     TIMESTAMP(TZ) NOT NULL              │
│ updated_at     TIMESTAMP(TZ) NOT NULL              │
└──────────┬──────────────────────────────────────┘
           │ 1:N (charger_id FK, CASCADE DELETE)
           │
     ┌─────┼──────────────────┐
     ▼                        ▼
┌──────────────────┐   ┌──────────────────┐
│    sessions      │   │  command_logs    │
├──────────────────┤   ├──────────────────┤
│ id          PK   │   │ id          PK   │
│ charger_id  FK   │   │ charger_id  FK   │
│ transaction_id   │   │ command          │
│ id_tag           │   │ payload    JSON  │
│ connector_id     │   │ status           │
│ evse_id          │   │ ocpp_version     │
│ meter_start      │   │ created_at       │
│ meter_stop       │   └──────────────────┘
│ start_time       │
│ stop_time        │
│ stop_reason      │
│ energy_kwh       │
│ created_at       │
└───────┬──────────┘
        │ 1:N (session_id FK, CASCADE DELETE)
        ▼
┌──────────────────┐
│  meter_values    │
├──────────────────┤
│ id          PK   │
│ session_id  FK   │
│ charger_id  FK   │
│ connector_id     │
│ evse_id          │
│ timestamp        │
│ energy_wh        │
│ power_w          │
│ voltage          │
│ current_a        │
│ soc              │
│ raw_json   JSON  │
└──────────────────┘
```

**All foreign keys use `CASCADE DELETE`** — deleting a charger removes all its sessions, meter values, and command logs.

---

## 7. API Reference

### Charger Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chargers` | List all chargers |
| `GET` | `/api/chargers/<id>` | Get single charger |
| `POST` | `/api/chargers` | Register new charger |
| `PUT` | `/api/chargers/<id>` | Update charger fields |
| `DELETE` | `/api/chargers/<id>` | Delete charger + cascade |

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sessions` | List all sessions (limit 100) |
| `GET` | `/api/sessions/<id>` | Get single session |
| `GET` | `/api/sessions/active` | List active (unstopped) sessions |
| `POST` | `/api/sessions/<id>/stop` | Remote stop a session |
| `GET` | `/api/chargers/<id>/sessions` | Sessions for a charger |

### Remote Commands

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chargers/<id>/start` | RemoteStartTransaction |
| `POST` | `/api/chargers/<id>/stop` | RemoteStopTransaction |
| `POST` | `/api/chargers/<id>/reset` | Reset (Soft/Hard) |
| `POST` | `/api/chargers/<id>/unlock` | UnlockConnector |
| `GET` | `/api/chargers/<id>/commands` | Command history log |

### Telemetry & Stats

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chargers/<id>/meter-values` | Meter readings |
| `GET` | `/api/chargers/<id>/meter-values/latest` | Latest reading |
| `GET` | `/api/sessions/<id>/meter-values` | Readings for session |
| `GET` | `/api/stats` | Platform-wide dashboard stats |
| `GET` | `/api/chargers/<id>/stats` | Per-charger statistics |

### Live Updates

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/live/snapshot` | Point-in-time state |
| `GET` | `/api/live/stream` | SSE event stream |
| `GET` | `/api/health` | Health check |

---

## 8. Deployment Architecture

### Docker Compose Services

| Service | Container | Image | Port | Role |
|---------|-----------|-------|------|------|
| HAProxy | `exxomatic-haproxy` | `haproxy:2.9-alpine` | 80 | Gateway |
| API | `exxomatic-server` | Custom (Python 3.12) | 5050 | REST API |
| Frontend | `exxomatic-frontend` | Custom (Node 20) | 3000 | Dashboard |
| Core WS | `exxomatic-ocpp-core` | Custom (Python 3.12) | 5000 | Production OCPP |
| Echo | `exxomatic-ocpp-echo` | Custom (Python 3.12) | 8000 | Debug Echo 1 |
| Echo-N | `exxomatic-ocpp-echo-n` | Custom (Python 3.12) | 5001 | Debug Echo 2 |

### Network

All services communicate over a `bridge` network (`exxomatic-net`). Only HAProxy port 80 is exposed externally.

---

## 10. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Protocol** | OCPP | 1.6J + 2.0.1 |
| **WebSocket** | `websockets` | ≥13.0 |
| **OCPP Library** | `ocpp` (Python) | ≥2.1.0 |
| **API Framework** | Flask | ≥3.0 |
| **WSGI Server** | Gunicorn (gthread) | ≥22.0 |
| **ORM** | SQLAlchemy | ≥2.0 |
| **Database** | PostgreSQL (prod) / SQLite (dev) | — |
| **Frontend** | Next.js + TypeScript + Tailwind | — |
| **Reverse Proxy** | HAProxy | 2.9 |
| **Containerization** | Docker Compose | — |
| **Runtime** | Python 3.12 / Node 20 | — |

---

*Generated by deep scan analysis — 2026-04-21*
