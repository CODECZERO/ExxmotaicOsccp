# Exxomatic OCPP — EV Charger Management System

A production-grade EV charger backend built natively on the OCPP protocol. Physical chargers connect via WebSocket, a Flask REST API serves dashboards and mobile apps, and PostgreSQL stores all state. This architecture natively unifies OCPP 1.6J and OCPP 2.0.1 directly interacting with the identical database structure.

**Live Production Dashboard:** [https://exxomatic.therisewebd.in](https://exxomatic.therisewebd.in)

---

## ⚡ How to Connect Chargers (Sending Data)

Physical chargers and testing simulators connect to the server using WebSockets. HAProxy cleanly accepts the traffic on Port 80 and routes it to the correct backend depending on the path.

### Live Production WebSocket URLs
These are the endpoints you should paste into your EV Hardware interface (or use for script testing):

*   **Production OCPP 1.6J:** `ws://exxomatic.therisewebd.in/ocpp/1.6/<CHARGER_NAME>`
*   **Production OCPP 2.0.1:** `ws://exxomatic.therisewebd.in/ocpp/2.0.1/<CHARGER_NAME>`
*   **Debug/Echo Server:** `ws://exxomatic.therisewebd.in/ocpp-echo/1.6/<CHARGER_NAME>`

### How to test using wscat (Console Simulator)
You can instantly simulate an EV charger and send data to the live server using `wscat`.

```bash
# 1. Install wscat globally if you don't have it
npm install -g wscat

# 2. Connect a simulated OCPP 1.6 Charger to the LIVE Server
wscat -c ws://exxomatic.therisewebd.in/ocpp/1.6/DEMO_CHARGER_001 --subprotocol ocpp1.6

# 3. Send a BootNotification payload inside the wscat terminal:
[2, "msg-001", "BootNotification", {"chargePointVendor": "VendorX", "chargePointModel": "ModelY"}]

# 4. Check the Dashboard website to watch it appear automatically!
```

---

## 🚀 Production Deployment (AWS EC2 + Cloudflare)

Because AWS Free-Tier servers easily crash during heavy compilation, this repository uses an optimized "Build Locally → Transfer" pipeline.

### Step 1: Bake the Frontend (On your local Laptop)
Next.js statically bakes API routes during compilation. You must run this locally before pushing.
```bash
cd web-client
# (Ensure Next.js is configured to use the proxy path in web-client/.env.local)
# NEXT_PUBLIC_API_URL=/api
npm run build
cd ..
```

### Step 2: Transfer to AWS (rsync)
Use `rsync` to push your code over SSH. 
***Crucial:*** *Do NOT simply exclude `node_modules`. Next.js relies on an isolated `node_modules` inside the `.next` output directory. Only exclude the root directories as shown below!*

```bash
rsync -avz \
        --exclude '/node_modules' \
        --exclude '/web-client/node_modules' \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '.pytest_cache' \
        --exclude '*.pyc' \
        --exclude '*.log' \
        --exclude 'logs/' \
        -e "ssh -i ./FleetServer.pem" \
        /home/codeczero/Desktop/FullStack/exxmotaicOSCCP \
        ubuntu@<YOUR_EC2_IP>:/home/ubuntu/
```

### Step 3: Run on AWS
SSH into your AWS instance and reboot the stack. HAProxy will automatically spin up.
```bash
docker-compose up -d --build

# HAProxy waits 30 seconds for Next.js to turn "Healthy" before routing traffic.
```

### Step 4: Configure Cloudflare
1.  Set DNS A-Record to point to your AWS EC2 IP.
2.  Go to **Cloudflare SSL/TLS Settings** and set encryption mode to **"Flexible"**. (Since HAProxy handles traffic natively on Port 80, Full encryption will fail).
3.  Ensure AWS Security Groups have Port 80 and Port 443 open.

---

## 🏗 System Architecture

```text
Internet → Cloudflare → HAProxy :80 → Flask API  :5050
                                     → Next.js    :3000
Charger  → Cloudflare → HAProxy :80 → OCPP Core  :5000
```

| Service | Port | Purpose |
|---|---|---|
| haproxy | 80 | Reverse proxy — routes all incoming traffic from Cloudflare via Host/Path |
| server (api) | 5050 | Flask REST API — Dashboard logic and SQLAlchemy DB management |
| frontend | 3000 | Next.js dashboard — Server-rendered UI |
| ocpp-core | 5000 | Production OCPP WebSocket server — unified V1.6/V20 |
| ocpp-echo | 8000 | Debug echo WebSocket server |

### HTTP REST API Endpoints (Frontend Use)
The API is stateless and communicates directly to PostgreSQL. Cloudflare routes requests to `/api` directly to Flask.

| Endpoint | Purpose |
|---|---|
| `GET  /api/health` | Verifies server boot |
| `GET  /api/stats` | Platform-wide aggregation |
| `GET  /api/chargers/<id>` | Hardware info & status |
| `GET  /api/sessions/<id>` | Charging session detail & energy consumed |
| `POST /api/chargers/<id>/stop` | Remotely stop an active session |
| `POST /api/chargers/<id>/reset` | Trigger a remote soft/hard hardware reboot |

---

## 🗄 Database Schema (PostgreSQL)

4 foundational tables managed via pure SQLAlchemy ORM mappings natively:

| Table | Function | Important Columns |
|---|---|---|
| `chargers` | Enrolled Hardware | `charger_id`, `vendor`, `model`, `status`, `last_heartbeat` |
| `sessions` | Active/Historical loads | `transaction_id`, `start_time`, `stop_time`, `energy_kwh` |
| `meter_values` | Periodical HW limits | `session_id`, `power_w`, `voltage`, `current_a`, `soc` |
| `command_logs` | Remote execution trace | `command`, `status`, `payload` |

---

## 💻 Local Development Setup

If you want to run the stack natively on your laptop without Docker for debugging:

```bash
# 1. Virtual Env & Python Dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Frontend Dependencies
cd web-client && npm install && cd ..

# 3. Environment & Database
cp .env.example .env
python init_db.py
```

Run the three core services in separate terminal panes:
```bash
python -m api.main        # Starts API (port 5050)
python -m core.main       # Starts WebSockets (port 5000)
cd web-client && npm run dev  # Starts UI (port 3000)
```