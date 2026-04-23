# Exxomatic OCPP — EV Charger Management System

A production-grade EV charger backend built natively on the OCPP protocol. Physical chargers connect via WebSocket, a Flask REST API serves dashboards and mobile apps, and PostgreSQL stores all state. This architecture natively unifies OCPP 1.6J and OCPP 2.0.1 directly interacting with the identical database structure.

**Live Production Dashboard:** [https://exxomatic.therisewebd.in](https://exxomatic.therisewebd.in)

---

## ⚡ How to Connect Chargers (Sending Data)

Physical chargers and testing simulators connect to the server using secure WebSockets (WSS). HAProxy terminates TLS with a Let's Encrypt certificate and routes traffic to the correct backend depending on the path.

### Live Production WebSocket URLs
These are the endpoints you should paste into your EV Hardware interface (or use for script testing). Use your primary domain (e.g., `exxocharger.exxomatic.in`).

*   **Production OCPP 1.6J:** `wss://<YOUR_DOMAIN>/ocpp/1.6/<CHARGER_NAME>`
*   **Production OCPP 2.0.1:** `wss://<YOUR_DOMAIN>/ocpp/2.0.1/<CHARGER_NAME>`
*   **Debug Echo Server (V16):** `wss://<YOUR_DOMAIN>/ocpp-echo/1.6/<CHARGER_NAME>`
*   **Debug Echo Server (V201):** `wss://<YOUR_DOMAIN>/ocpp-echo/2.0.1/<CHARGER_NAME>`
*   **Debug Echo-N Server (V16):** `wss://<YOUR_DOMAIN>/ocpp-echo-n/1.6/<CHARGER_NAME>`
*   **Debug Echo-N Server (V201):** `wss://<YOUR_DOMAIN>/ocpp-echo-n/2.0.1/<CHARGER_NAME>`

*(Example domains: `exxocharger.exxomatic.in` or `exxomatic.therisewebd.in`)*

### How to test using wscat (Console Simulator)
You can instantly simulate an EV charger and send data to the live server using `wscat`. The **Core** server saves data to the database and updates the dashboard, while the **Echo** servers simply log and mirror your messages for debugging.

```bash
# 1. Install wscat globally if you don't have it
npm install -g wscat

# 2. Connect a simulated OCPP 1.6 Charger to the LIVE Core Server
wscat -c wss://exxocharger.exxomatic.in/ocpp/1.6/DEMO_CHARGER_001 --subprotocol ocpp1.6

# 3. Send a BootNotification payload inside the wscat terminal:
[2, "msg-001", "BootNotification", {"chargePointVendor": "VendorX", "chargePointModel": "ModelY"}]

# 4. Check the Dashboard website to watch it appear automatically!

# 5. Send a Heartbeat to keep the connection alive:
[2, "msg-002", "Heartbeat", {}]
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

### Step 4: SSL Setup (Let's Encrypt)

The stack auto-configures Let's Encrypt SSL certificates. It supports **TWO modes**, auto-detected based on your `.env` file:

#### Mode A: Universal (HTTP-01) — Works with ANY Domain
This mode requires no API tokens. It works as long as your domain points to the server and Port 80 is open.

**Setup:**
1. Ensure your domain's DNS A-Record points to your EC2 instance's IP.
2. In your `.env` file, leave `CLOUDFLARE_API_TOKEN` empty:
   ```bash
   DOMAIN_NAME=yourdomain.com
   LETSENCRYPT_EMAIL=admin@yourdomain.com
   CLOUDFLARE_API_TOKEN=
   ```
3. Deploy the stack: `docker-compose up -d --build`
4. *(If using Cloudflare)*: You must set the DNS record to **"DNS Only" (Grey Cloud)** temporarily during the first setup, or disable "Always Use HTTPS" so the ACME challenge on port 80 can reach the server. Once the cert is issued, you can turn the proxy (Orange Cloud) back on and set SSL to "Full (Strict)".

#### Mode B: Cloudflare (DNS-01) — Supports Wildcards
If your domain is managed by Cloudflare, this mode is recommended. It works even if the server is fully firewalled, supports wildcard certificates, and requires no DNS toggling.

**Setup:**
1. Create a Cloudflare API Token at https://dash.cloudflare.com/profile/api-tokens (Use the **"Edit zone DNS"** template).
2. Add it to your `.env` file:
   ```bash
   DOMAIN_NAME=exxomatic.therisewebd.in
   LETSENCRYPT_EMAIL=admin@example.com
   CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
   ```
3. Deploy the stack: `docker-compose up -d --build`
4. Set your Cloudflare SSL/TLS mode to **"Full (Strict)"**.

> **Note for both modes:** The certbot container auto-renews every 12 hours and hot-reloads HAProxy with zero downtime. Certificates are persisted in a Docker volume, surviving container restarts.

---

## 🏗 System Architecture

```text
Browser  → Cloudflare (TLS) → HAProxy :443 (TLS) → Flask API  :5050
                                                   → Next.js    :3000
Charger  → Cloudflare (TLS) → HAProxy :443 (TLS) → OCPP Core  :5000
                              (HTTP :80 → 301 redirect to HTTPS)
```

| Service | Port | Purpose |
|---|---|---|
| haproxy | 80, 443 | Reverse proxy — TLS termination with Let's Encrypt, HTTP→HTTPS redirect |
| server (api) | 5050 | Flask REST API — Dashboard logic and DB management |
| frontend | 3000 | Next.js dashboard — UI with 0.5s real-time refresh |
| ocpp-core | 5000 | Production OCPP WebSocket server — unified V1.6/V20.1 |
| ocpp-echo | 8000 | Engineering Sandbox Server (Standard 1.6 focus) |
| ocpp-echo-n | 5001 | Engineering Sandbox Server (Standard 2.0.1 focus) |

### 🔌 OCPP Hardware Connection URLs

Provide these links to your hardware chargers or engineering team. Ensure you replace `YOUR_CHARGER_ID` with the actual identifier.

**1. Production Core Server (The Real Unified System)**
Use this for actual production deployment. The server automatically conforms to the format you request:
*   **OCPP 1.6 Devices:** `wss://YOUR_DOMAIN/ocpp/1.6/YOUR_CHARGER_ID`
*   **OCPP 2.0.1 Devices:** `wss://YOUR_DOMAIN/ocpp/2.0.1/YOUR_CHARGER_ID`

**2. Echo Server (Engineering Sandbox for OCPP 1.6 only)**
Use this strictly for debugging 1.6 standard hardware. It will **reject** 2.0.1 connections.
*   **Connection URL:** `wss://YOUR_DOMAIN/ocpp-echo/1.6/YOUR_CHARGER_ID`

**3. Echo-N Server (Engineering Sandbox for OCPP 2.0.1 only)**
Use this strictly for testing new 2.0.1 standard hardware. It will **reject** 1.6 connections.
*   **Connection URL:** `wss://YOUR_DOMAIN/ocpp-echo-n/2.0.1/YOUR_CHARGER_ID`

### 📱 Main App URL (Frontend Dashboard)
Simply visit this in your web browser to manage your platform:
*   **Dashboard URL:** `https://YOUR_DOMAIN`

### HTTP REST API Endpoints (Frontend Use)
The API is stateless and communicates directly to PostgreSQL. Cloudflare routes requests to `/api` directly to Flask.

| Endpoint | Purpose |
|---|---|
| `GET  /api/health` | Verifies server boot |
| `GET  /api/stats` | Platform-wide aggregation |
| `GET  /api/chargers/<id>` | Hardware info & status |
| `GET  /api/sessions/<id>` | Charging session detail & energy consumed |
| `GET  /api/live/snapshot` | **NEW**: Point-in-time dashboard state (instant load) |
| `GET  /api/live/stream` | **SSE**: Real-time 0.5s pulse stream |
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
python scripts/init_db.py
```

Run the core services in separate terminal panes:
```bash
python -m api.main          # Starts API (port 5050)
python -m core.main         # Starts WebSockets (port 5000)
cd web-client && npm run dev # Starts UI (port 3000)
```

### 🛠 Troubleshooting & Maintenance

If the server accumulates too many "Pending" commands (causing timeouts):
```bash
# Clean up stale commands (FIFO stability)
python tests/cleanup_stale_commands.py
```

To run a verbose local hardware simulation (ABB Terra simulator):
```bash
python tests/test_local.py
```

### 🧪 Remote Diagnostics
To run a full production sanity check against the cloud:
```bash
python tests/test_remote_servers.py
```