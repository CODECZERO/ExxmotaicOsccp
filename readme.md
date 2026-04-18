# Exxomatic OCPP — EV Charger Management System

A production-grade EV charger backend built natively on the OCPP protocol. Physical chargers connect via WebSocket, a Flask REST API serves dashboards and mobile apps, and PostgreSQL stores all state. This architecture natively unifies OCPP 1.6J and OCPP 2.0.1 directly interacting with the identical database structure.

---

## Architecture

```text
Internet → Cloudflare → HAProxy :80 → Flask API  :5050
Charger  → Cloudflare → HAProxy :80 → OCPP Core  :5000
```

| Service | Port | Purpose |
|---|---|---|
| core | 5000 | Production OCPP WebSocket server — actual EV hardware endpoints |
| api | 5050 | Flask REST API — HTTP endpoints for dashboards and mobile apps |
| echo | 8000 | Debug echo WebSocket server (Dual Protocol 1.6 / 2.0.1) |
| echo-n | 5001 | Alternate debug echo WebSocket server (Dual Protocol 1.6 / 2.0.1) |

---

## HTTP REST API Endpoints

The API is fully stateless, speaking directly to PostgreSQL. Start the API using `python api/main.py`. Base URL is `http://localhost:5050/api`.

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

**Starting the Socket servers:**
```bash
python core/main.py   # Production
python echo/main.py   # Dry-Run Tester
```

**Hardware Connect URLs:**
```text
ws://localhost:5000/ocpp/1.6/YOUR_CHARGER_ID
ws://localhost:5000/ocpp/2.0.1/YOUR_CHARGER_ID
```

**Testing via Console Websocket Client (`wscat`):**
To simulate an OCPP 1.6 charger connecting to your Echo testing node:
```bash
wscat -c ws://localhost:8000/ocpp/1.6/TEST001 --subprotocol ocpp1.6
```
To simulate an OCPP 2.0.1 charger:
```bash
wscat -c ws://localhost:8000/ocpp/2.0.1/TEST002 --subprotocol ocpp2.0.1
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

## Local Development & Setup

```bash
# 1. Clone
git clone https://github.com/CODECZERO/ExxmotaicOsccp.git
cd ExxmotaicOsccp

# 2. Virtual Env
python -m venv .venv
source .venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Generate Env File
cp .env.example .env
# Important: Update DATABASE_URL with a local PostgreSQL server

# 5. Run full test suite to guarantee functionality
pytest tests/ -v

# 6. Execute desired environments
python api/main.py       # REST
python core/main.py      # Core WebSockets
```