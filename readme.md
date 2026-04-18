# Exxomatic OCPP — EV Charger Management System

A production-grade EV charger backend built natively on the OCPP protocol. Physical chargers connect via WebSocket, a Flask REST API serves dashboards and mobile apps, and PostgreSQL stores all state. This architecture natively unifies OCPP 1.6J and OCPP 2.0.1 directly interacting with the identical database structure.

---

## Architecture

```text
Internet → Cloudflare → HAProxy :80 → Flask API  :5050
                                     → Next.js    :3000
Charger  → Cloudflare → HAProxy :80 → OCPP Core  :5000
```

| Service | Port | Purpose |
|---|---|---|
| haproxy | 80 | Reverse proxy — hostname + path routing |
| server (api) | 5050 | Flask REST API — HTTP endpoints for dashboards and mobile apps |
| frontend | 3000 | Next.js dashboard — real-time EV infrastructure UI |
| ocpp-core | 5000 | Production OCPP WebSocket server — actual EV hardware endpoints |
| ocpp-echo | 8000 | Debug echo WebSocket server (dual OCPP 1.6 / 2.0.1) |
| ocpp-echo-n | 5001 | Alternate debug echo WebSocket server (dual OCPP 1.6 / 2.0.1) |

---

## Quick Start — Docker (Recommended)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

### 1. Clone & Configure

```bash
git clone https://github.com/CODECZERO/ExxmotaicOsccp.git
cd ExxmotaicOsccp

# Create your environment file
cp .env.example .env
# Important: Update DATABASE_URL with your PostgreSQL connection string
```

### 2. Build & Run

```bash
# Build all containers and start the full stack
docker compose up --build

# Or run in background (detached)
docker compose up --build -d
```

### 3. Access the Platform

| URL | Service |
|-----|---------|
| `http://localhost` | Dashboard (Next.js frontend) |
| `http://localhost/api/health` | API health check |
| `http://localhost/api/chargers` | Charger registry API |
| `ws://localhost/ocpp/1.6/<CHARGER_ID>` | OCPP 1.6J WebSocket |
| `ws://localhost/ocpp/2.0.1/<CHARGER_ID>` | OCPP 2.0.1 WebSocket |

### 4. Useful Commands

```bash
# View logs from all services
docker compose logs -f

# View logs from a specific service
docker compose logs -f server

# Stop all services
docker compose down

# Rebuild a specific service
docker compose build server
docker compose up -d server

# Initialize / reset the database
docker compose exec server python init_db.py
```

---

## Docker Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
│                     (exxomatic-net)                           │
│                                                              │
│  ┌──────────────┐                                            │
│  │   HAProxy    │ :80                                        │
│  │  (Gateway)   │                                            │
│  └──────┬───────┘                                            │
│         │                                                    │
│    ┌────┴──────┬──────────┬───────────┬───────────┐          │
│    │           │          │           │           │          │
│    ▼           ▼          ▼           ▼           ▼          │
│ ┌──────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐    │
│ │Server│ │Frontend │ │  OCPP  │ │  Echo  │ │ Echo-N   │    │
│ │:5050 │ │ :3000   │ │ :5000  │ │ :8000  │ │  :5001   │    │
│ └──┬───┘ └─────────┘ └───┬────┘ └───┬────┘ └────┬─────┘    │
│    │                     │          │           │          │
│    └──────────┬──────────┴──────────┴───────────┘          │
│               │                                            │
│               ▼                                            │
│       ┌──────────────┐                                     │
│       │  PostgreSQL  │ (External: Aiven Cloud)             │
│       │    :5432     │                                     │
│       └──────────────┘                                     │
└──────────────────────────────────────────────────────────────┘
```

### HAProxy Routing Rules

| Condition | Backend |
|-----------|---------|
| Host: `charger-api.exxomatic.in` | → server :5050 |
| Path starts with `/api/` | → server :5050 |
| WebSocket + path `/ocpp/` | → ocpp-core :5000 |
| WebSocket + path `/ocpp-echo/` | → ocpp-echo :8000 |
| WebSocket + path `/ocpp-echo-n/` | → ocpp-echo-n :5001 |
| Everything else | → frontend :3000 |

### Container Details

| Container | Image | Dockerfile | Health Check |
|-----------|-------|------------|--------------|
| `exxomatic-haproxy` | `haproxy:2.9-alpine` | — (official image) | Depends on server + frontend |
| `exxomatic-server` | `python:3.12-slim` | `server/Dockerfile` | `GET /api/health` |
| `exxomatic-frontend` | `node:20-alpine` | `web-client/Dockerfile` | `GET /` |
| `exxomatic-ocpp-core` | `python:3.12-slim` | `server/Dockerfile` | — |
| `exxomatic-ocpp-echo` | `python:3.12-slim` | `server/Dockerfile` | — |
| `exxomatic-ocpp-echo-n` | `python:3.12-slim` | `server/Dockerfile` | — |

---

## HTTP REST API Endpoints

The API is fully stateless, speaking directly to PostgreSQL. Base URL is `http://localhost/api` (via HAProxy) or `http://localhost:5050/api` (direct).

### Platform Stats (Dashboards)
```text
GET    /stats                     platform-wide aggregation dashboard
GET    /chargers/<id>/stats       statistics for a specific charger
```

### Chargers (Management)
```text
GET    /chargers                  list all registered external chargers
GET    /chargers/<id>             get single charger hardware + connection status
POST   /chargers                  register a new physical charger
PUT    /chargers/<id>             update existing charger attributes
DELETE /chargers/<id>             remove charger permanently
GET    /chargers/<id>/sessions    retrieve all sessions executed by this charger
```

### Charging Sessions (Transactions)
```text
GET    /sessions                  list all unified charging sessions
GET    /sessions/<id>             session detail + total energy consumed constraints
GET    /sessions/active           all active sessions currently drawing load
POST   /sessions/<id>/stop        remotely stop an active session
```

### Remote Commands (Hardware Triggers)
Tracks all commands inside the `command_logs` DB table.
```text
POST   /chargers/<id>/start       send a RemoteStartTransaction to charger
POST   /chargers/<id>/stop        send a RemoteStopTransaction to charger
POST   /chargers/<id>/reset       send a Soft/Hard Reset to reboot charger
POST   /chargers/<id>/unlock      send UnlockConnector command
GET    /chargers/<id>/commands    view the complete command execution history footprint
```

### Meter Values (Live Load)
```text
GET    /chargers/<id>/meter-values/latest  view the exact last live reading
GET    /chargers/<id>/meter-values         view all historical meter readings for a specific charger
GET    /sessions/<id>/meter-values         view all reading footprints traced to a specific session
```

### Health
```text
GET    /health                    HAProxy health check verification
```

---

## WebSocket Interfaces (OCPP Sockets)

Both the `core` production server and `echo` testing servers dynamically identify versions based on the URL sequence.
They automatically support **OCPP 1.6J** and **OCPP 2.0.1** on the exact same port.

**Hardware Connect URLs (via HAProxy):**
```text
ws://localhost/ocpp/1.6/YOUR_CHARGER_ID
ws://localhost/ocpp/2.0.1/YOUR_CHARGER_ID
```

**Direct Connect URLs (bypassing HAProxy):**
```text
ws://localhost:5000/ocpp/1.6/YOUR_CHARGER_ID
ws://localhost:5000/ocpp/2.0.1/YOUR_CHARGER_ID
```

**Testing via Console Websocket Client (`wscat`):**
```bash
# OCPP 1.6 charger simulation
wscat -c ws://localhost/ocpp/1.6/TEST001 --subprotocol ocpp1.6

# OCPP 2.0.1 charger simulation
wscat -c ws://localhost/ocpp/2.0.1/TEST002 --subprotocol ocpp2.0.1
```

---

## Database Schema Model (PostgreSQL)

4 foundational tables managed via pure SQLAlchemy ORM mappings natively:

| Table | Function | Important Columns |
|---|---|---|
| `chargers` | Enrolled Hardware | `charger_id`, `vendor`, `model`, `status`, `last_heartbeat` |
| `sessions` | Active/Historical loads | `transaction_id`, `start_time`, `stop_time`, `energy_kwh` |
| `meter_values` | Periodical HW limits | `session_id`, `power_w`, `voltage`, `current_a`, `soc` |
| `command_logs` | Remote execution trace | `command`, `status`, `payload` |

(All internal keys utilize implicit SQLAlchemy `ForeignKey()` arrays avoiding mapping issues).

---

## Local Development (Without Docker)

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL (or use Aiven cloud)

### Setup

```bash
# 1. Clone
git clone https://github.com/CODECZERO/ExxmotaicOsccp.git
cd ExxmotaicOsccp

# 2. Virtual Env
python -m venv .venv
source .venv/bin/activate

# 3. Python Dependencies
pip install -r requirements.txt

# 4. Frontend Dependencies
cd web-client && npm install && cd ..

# 5. Environment
cp .env.example .env
# Important: Update DATABASE_URL with a PostgreSQL connection string

# 6. Initialize Database Tables
python init_db.py
```

### Run Services

Open 3 terminals:

```bash
# Terminal 1 — Backend API (port 5050)
source .venv/bin/activate
python -m api.main

# Terminal 2 — Frontend (port 3000)
cd web-client
npm run dev

# Terminal 3 — OCPP WebSocket Server (port 5000, optional)
source .venv/bin/activate
python -m core.main
```

### Run Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

---

## Project Structure

```
exxmotaicOSCCP/
├── api/                    # Flask REST API
│   ├── __init__.py         # App factory
│   ├── main.py             # Dev entry point
│   ├── decorators.py       # Error handler decorator
│   ├── controllers/        # Business logic
│   └── routes/             # Blueprint route definitions
├── core/                   # OCPP WebSocket Server
│   ├── main.py             # WebSocket entry point
│   ├── router.py           # Version detection + CP factory
│   ├── V16/                # OCPP 1.6J handlers
│   └── V20/                # OCPP 2.0.1 handlers
├── shared/                 # Cross-service utilities
│   ├── constants.py        # Central config
│   ├── env.py              # .env loader
│   ├── normalizer.py       # Version-agnostic data mapping
│   ├── live_state.py       # Session + meter helpers
│   └── db/                 # SQLAlchemy models + client
├── server/                 # Docker server config
│   ├── Dockerfile          # Python API container
│   ├── gunicorn.conf.py    # Gunicorn production settings
│   └── entrypoint.sh       # Container startup script
├── web-client/             # Next.js frontend
│   ├── Dockerfile          # Frontend container
│   ├── src/app/            # Pages (dashboard, sites, sessions)
│   ├── src/components/     # Reusable UI components
│   ├── src/hooks/          # SWR data hooks + live stream
│   └── src/lib/            # API client, types, formatting
├── haproxy/                # Reverse proxy config
│   └── haproxy.cfg         # Routing rules
├── echo/                   # Debug echo server (dev-only)
├── echo-n/                 # Alternate debug echo (dev-only)
├── docker-compose.yml      # Full-stack orchestration
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── init_db.py              # Database table creation
└── tests/                  # Integration tests
```