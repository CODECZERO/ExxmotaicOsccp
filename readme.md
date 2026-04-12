# Exxomatic OCPP — EV Charger Management System

A production-grade EV charger backend built on the OCPP protocol. Physical chargers connect via WebSocket, a Flask REST API serves dashboards and mobile apps, and PostgreSQL stores all state.

---

## Architecture

```
Internet → Cloudflare → HAProxy :80 → Flask API  :5050
Charger  → Cloudflare → HAProxy :80 → OCPP Core  :5000
```

| Service | Port | Purpose |
|---|---|---|
| core | 5000 | OCPP WebSocket server — chargers connect here |
| api | 5050 | Flask REST API — dashboards and apps connect here |
| echo | 8000 | Debug echo server for hardware testing (v1.6J) |
| echo_n | 5001 | Debug echo server for hardware testing (v2.0.1) |

---

## Folder Structure

```
exxomatic-ocpp/
│
├── core/                        ← OCPP WebSocket server :5000
│   ├── main.py                  ← entry point
│   ├── router.py                ← detects version, routes to handler
│   └── handlers/
│       ├── v16/
│       │   ├── __init__.py
│       │   ├── boot_notification.py
│       │   ├── heartbeat.py
│       │   ├── start_transaction.py
│       │   ├── stop_transaction.py
│       │   ├── status_notification.py
│       │   ├── meter_values.py
│       │   └── authorize.py
│       └── v201/
│           ├── __init__.py
│           ├── boot_notification.py
│           ├── heartbeat.py
│           ├── transaction_event.py
│           ├── status_notification.py
│           ├── meter_values.py
│           └── notify_event.py
│
├── api/                         ← Flask REST API :5050
│   ├── main.py                  ← entry point, Flask app factory
│   ├── decorators.py            ← error_handler decorator
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chargers.py
│   │   ├── sessions.py
│   │   ├── commands.py
│   │   └── health.py
│   ├── controllers/
│   │   ├── charger_controller.py
│   │   ├── session_controller.py
│   │   └── command_controller.py
│   └── templates/
│       └── error.html
│
├── echo/                        ← debug echo server :8000
│   └── main.py
│
├── echo_n/                      ← debug echo v2.0.1 :5001
│   └── main.py
│
├── shared/                      ← imported by all services
│   ├── __init__.py
│   ├── logger.py                ← RotatingFileHandler setup
│   ├── db/
│   │   ├── __init__.py
│   │   ├── client.py            ← SQLAlchemy session
│   │   └── models.py            ← chargers, sessions, meter_values
│   ├── types/
│   │   ├── __init__.py
│   │   ├── ocpp16_types.py      ← dataclasses for 1.6J payloads
│   │   └── ocpp201_types.py     ← dataclasses for 2.0.1 payloads
│   └── constants.py
│
├── logs/                        ← auto-created at runtime, never commit
├── tests/
├── docker-compose.yml
├── requirements.txt
├── config.py
├── .env                         ← never commit
├── .env.example                 ← commit this
└── .gitignore
```

---

## OCPP Version Support

| Version | Status | Notes |
|---|---|---|
| OCPP 1.6J | Primary | 90% of Indian chargers, build this first |
| OCPP 2.0.1 | Secondary | Add when a 2.0.1 charger is available for testing |

Chargers announce their version in the WebSocket URL:

```
ws://host/ocpp/1.6/CHARGER_ID     → routes to handlers/v16/
ws://host/ocpp/2.0.1/CHARGER_ID   → routes to handlers/v201/
```

---

## REST API Endpoints

### Chargers
```
GET    /api/chargers              list all chargers
GET    /api/chargers/<id>         get single charger + status
POST   /api/chargers              register new charger
PUT    /api/chargers/<id>         update charger
DELETE /api/chargers/<id>         remove charger
```

### Sessions
```
GET    /api/sessions              list all sessions
GET    /api/sessions/<id>         session detail + energy consumed
GET    /api/sessions/active       all active sessions
POST   /api/sessions/<id>/stop    stop a session
```

### Commands
```
POST   /api/chargers/<id>/start   remote start session
POST   /api/chargers/<id>/stop    remote stop session
POST   /api/chargers/<id>/reset   reset charger
POST   /api/chargers/<id>/unlock  unlock connector
```

### Health
```
GET    /health                    HAProxy health check
```

---

## Database Schema

Three tables — `chargers`, `sessions`, `meter_values`.

| Table | Key columns |
|---|---|
| chargers | id, charger_id, vendor, model, status, last_heartbeat |
| sessions | id, charger_id, transaction_id, id_tag, start_time, stop_time, energy_kwh |
| meter_values | id, session_id, timestamp, energy_wh, power_w, voltage, current |

Managed via SQLAlchemy. Models defined in `shared/db/models.py`.

---

## Local Setup

```bash
# 1. clone
git clone https://github.com/CODECZERO/ExxmotaicOsccp.git
cd ExxmotaicOsccp

# 2. create virtual env
python -m venv venv
source venv/bin/activate        # windows: venv\Scripts\activate

# 3. install dependencies
pip install -r requirements.txt

# 4. setup env
cp .env.example .env
# fill in DATABASE_URL, SECRET_KEY etc

# 5. run all services
docker-compose up

# 6. test echo server (no charger needed)
wscat -c ws://localhost:8000/ocpp/1.6/TEST001
```

---

## Running Individual Services

```bash
python core/main.py       # OCPP core :5000
python api/main.py        # Flask API :5050
python echo/main.py       # echo :8000
python echo_n/main.py     # echo-n :5001
```

---

## Git Branch Convention

```
main                          ← production, always stable
dev                           ← active development

feature/ocpp-core-router      ← new features
feature/v16-handlers
feature/flask-api-routes

fix/heartbeat-handler         ← bug fixes
chore/folder-structure        ← housekeeping
```

Always branch off `dev`. Never commit directly to `main`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| WebSocket server | Python `websockets` library |
| REST API | Flask |
| Database ORM | SQLAlchemy |
| Database | PostgreSQL |
| Reverse proxy | HAProxy |
| DNS + security | Cloudflare |
| Deployment | Docker + AWS EC2 |
| Logging | Python `logging` with `RotatingFileHandler` |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/exxomatic
SECRET_KEY=your-secret-key
API_KEY=your-api-key
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
CORE_PORT=5000
API_PORT=5050
ECHO_PORT=8000
ECHO_N_PORT=5001
```

---

## Build Priority

1. `shared/db/models.py` — define tables first
2. `core/handlers/v16/` — handle real charger messages
3. `api/routes/` — REST layer
4. `echo/main.py` — for hardware testing
5. `core/handlers/v201/` — only when a 2.0.1 charger is available

---

*Built by CODECZERO*