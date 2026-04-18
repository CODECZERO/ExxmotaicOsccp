import asyncio
import requests
import websockets
import json
from datetime import datetime, timezone

API_PORT = 5050
CORE_PORT = 5000
ECHO_PORT = 8000
ECHO_N_PORT = 5001

HTTP_URL = f"http://127.0.0.1:{API_PORT}"
WS_URL = "ws://127.0.0.1"

GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'


async def drain_buffer(ws, timeout=0.5):
    """Read all buffered messages, print them, and return count."""
    count = 0
    while True:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            parsed = json.loads(msg)
            if isinstance(parsed, list) and parsed[0] == 3:
                # CallResult - show the response
                print(f"   {DIM}<- Response [{parsed[1]}]: {json.dumps(parsed[2]) if len(parsed) > 2 else '{}'}{RESET}")
            elif isinstance(parsed, list) and parsed[0] == 4:
                # CallError
                print(f"   {RED}<- ERROR [{parsed[1]}]: {parsed[2]}: {parsed[3]}{RESET}")
            count += 1
        except asyncio.TimeoutError:
            break
    return count


async def wait_for_command(ws, expected_cmd):
    try:
        for _ in range(20):
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            parsed = json.loads(msg)
            if not isinstance(parsed, list):
                continue
            if parsed[0] == 3:
                continue
            if parsed[0] == 2:
                msg_id = parsed[1]
                cmd_name = parsed[2]
                cmd_payload = parsed[3] if len(parsed) > 3 else {}
                print(f"   {CYAN}<- COMMAND: {cmd_name} payload={json.dumps(cmd_payload)}{RESET}")
                if cmd_name == expected_cmd:
                    print(f"   {GREEN}✔ {expected_cmd} delivered!{RESET}")
                    await ws.send(json.dumps([3, msg_id, {"status": "Accepted"}]))
                    return True
                else:
                    print(f"   {YELLOW}  (stale — acking){RESET}")
                    await ws.send(json.dumps([3, msg_id, {"status": "Accepted"}]))
                    continue
        return False
    except asyncio.TimeoutError:
        print(f"   {RED}✘ Timeout waiting for {expected_cmd}{RESET}")
        return False


async def test_charger(name, port, path, cid, version):
    """Full lifecycle test with verbose output."""
    print(f"\n{'='*70}")
    print(f"{BOLD} {name}  ({path}/{version}/{cid}){RESET}")
    print(f"{'='*70}")

    url = f"{WS_URL}:{port}{path}/{version}/{cid}"
    sub = "ocpp1.6" if version == "1.6" else "ocpp2.0.1"

    try:
        async with websockets.connect(url, subprotocols=[sub], open_timeout=5) as ws:
            print(f"{GREEN}✔ WebSocket Connected (subprotocol: {sub}){RESET}")

            # ── BOOT ──
            if version == "1.6":
                boot = [2, "boot-1", "BootNotification", {
                    "chargePointVendor": "ABB",
                    "chargePointModel": "Terra AC W22-T-R-0",
                    "chargePointSerialNumber": "ABB-001-SN",
                    "firmwareVersion": "1.4.2"
                }]
            else:
                boot = [2, "boot-1", "BootNotification", {
                    "chargingStation": {
                        "vendorName": "ABB",
                        "model": "Terra AC W22-T-R-0",
                        "serialNumber": "ABB-001-SN",
                        "firmwareVersion": "2.1.0"
                    },
                    "reason": "PowerUp"
                }]
            print(f"\n{BOLD}── BOOT ──{RESET}")
            print(f"   -> {json.dumps(boot[3], indent=6)}")
            await ws.send(json.dumps(boot))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            resp_data = json.loads(resp)
            print(f"   {GREEN}<- Server accepted: {json.dumps(resp_data[2])}{RESET}")

            # ── STATUS ──
            print(f"\n{BOLD}── STATUS NOTIFICATION ──{RESET}")
            if version == "1.6":
                status = [2, "status-1", "StatusNotification", {
                    "connectorId": 1, "errorCode": "NoError", "status": "Charging"
                }]
            else:
                status = [2, "status-1", "StatusNotification", {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "connectorStatus": "Occupied",
                    "evseId": 1, "connectorId": 1
                }]
            print(f"   -> Connector 1: {'Charging' if version == '1.6' else 'Occupied'}")
            await ws.send(json.dumps(status))

            # ── START TRANSACTION ──
            print(f"\n{BOLD}── START TRANSACTION ──{RESET}")
            ts_start = datetime.now(tz=timezone.utc).isoformat()
            if version == "1.6":
                start = [2, "start-1", "StartTransaction", {
                    "connectorId": 1,
                    "idTag": "RFID-04E3B2A1",
                    "meterStart": 10500,
                    "timestamp": ts_start
                }]
                print(f"   -> RFID Tag: RFID-04E3B2A1")
                print(f"   -> Meter Start: 10,500 Wh")
                print(f"   -> Timestamp: {ts_start}")
            else:
                start = [2, "start-1", "TransactionEvent", {
                    "eventType": "Started",
                    "timestamp": ts_start,
                    "triggerReason": "Authorized",
                    "seqNo": 1,
                    "transactionInfo": {"transactionId": "TX-ABB-001"}
                }]
                print(f"   -> Transaction: TX-ABB-001")
                print(f"   -> Trigger: Authorized")
            await ws.send(json.dumps(start))

            # ── METER VALUES (mid-session) ──
            print(f"\n{BOLD}── METER VALUES (mid-session) ──{RESET}")
            ts_meter = datetime.now(tz=timezone.utc).isoformat()
            if version == "1.6":
                meter = [2, "meter-1", "MeterValues", {
                    "connectorId": 1,
                    "transactionId": 1,
                    "meterValue": [{
                        "timestamp": ts_meter,
                        "sampledValue": [
                            {"value": "13200", "unit": "Wh", "measurand": "Energy.Active.Import.Register"},
                            {"value": "7400", "unit": "W", "measurand": "Power.Active.Import"},
                            {"value": "230", "unit": "V", "measurand": "Voltage"},
                            {"value": "32", "unit": "A", "measurand": "Current.Import"},
                            {"value": "45", "unit": "Percent", "measurand": "SoC"}
                        ]
                    }]
                }]
                print(f"   -> Energy:  13,200 Wh (13.2 kWh)")
                print(f"   -> Power:   7,400 W (7.4 kW)")
                print(f"   -> Voltage: 230 V")
                print(f"   -> Current: 32 A")
                print(f"   -> SoC:     45%")
            else:
                meter = [2, "meter-1", "MeterValues", {
                    "evseId": 1,
                    "meterValue": [{
                        "timestamp": ts_meter,
                        "sampledValue": [
                            {"value": 13200.0, "measurand": "Energy.Active.Import.Register", "unitOfMeasure": {"unit": "Wh"}},
                            {"value": 7400.0, "measurand": "Power.Active.Import", "unitOfMeasure": {"unit": "W"}},
                            {"value": 230.5, "measurand": "Voltage", "unitOfMeasure": {"unit": "V"}},
                            {"value": 32.1, "measurand": "Current.Import", "unitOfMeasure": {"unit": "A"}},
                            {"value": 45.0, "measurand": "SoC", "unitOfMeasure": {"unit": "Percent"}}
                        ]
                    }]
                }]
                print(f"   -> Energy:  13,200 Wh (13.2 kWh)")
                print(f"   -> Power:   7,400 W (7.4 kW)")
                print(f"   -> Voltage: 230.5 V")
                print(f"   -> Current: 32.1 A")
                print(f"   -> SoC:     45%")
            await ws.send(json.dumps(meter))

            # ── STOP TRANSACTION (V2 only) ──
            if version != "1.6":
                print(f"\n{BOLD}── STOP TRANSACTION (TransactionEvent Ended) ──{RESET}")
                ts_stop = datetime.now(tz=timezone.utc).isoformat()
                stop = [2, "stop-1", "TransactionEvent", {
                    "eventType": "Ended",
                    "timestamp": ts_stop,
                    "triggerReason": "StopAuthorized",
                    "seqNo": 2,
                    "transactionInfo": {"transactionId": "TX-ABB-001"},
                    "meterValue": [{
                        "timestamp": ts_stop,
                        "sampledValue": [
                            {"value": 18500.0, "measurand": "Energy.Active.Import.Register"}
                        ]
                    }]
                }]
                print(f"   -> Final Energy: 18,500 Wh (18.5 kWh)")
                print(f"   -> Session Energy: 5,300 Wh (5.3 kWh delivered)")
                await ws.send(json.dumps(stop))

            # ── HEARTBEAT ──
            print(f"\n{BOLD}── HEARTBEAT ──{RESET}")
            await ws.send(json.dumps([2, "hb-1", "Heartbeat", {}]))

            # ── DRAIN ALL RESPONSES ──
            await asyncio.sleep(1)
            drained = await drain_buffer(ws, timeout=1.0)
            print(f"\n   {GREEN}✔ All {drained} server responses received{RESET}")

            # ── COMMAND DELIVERY (Core only) ──
            if path == "/ocpp":
                print(f"\n{BOLD}── REMOTE COMMAND DELIVERY ──{RESET}")
                
                print(f"\n   {YELLOW}Sending Reset command via REST API...{RESET}")
                r = requests.post(f"{HTTP_URL}/api/chargers/{cid}/reset",
                    json={"type": "Soft" if version == "1.6" else "OnIdle"}, timeout=5)
                print(f"   API Response: {r.json().get('message', r.json())}")
                c1 = await wait_for_command(ws, "Reset")

                if version == "1.6":
                    print(f"\n   {YELLOW}Sending RemoteStartTransaction via REST API...{RESET}")
                    r = requests.post(f"{HTTP_URL}/api/chargers/{cid}/start",
                        json={"id_tag": "RFID-NEW-USER", "connector_id": 1}, timeout=5)
                    print(f"   API Response: {r.json().get('message', r.json())}")
                    c2 = await wait_for_command(ws, "RemoteStartTransaction")

                    print(f"\n   {YELLOW}Sending RemoteStopTransaction via REST API...{RESET}")
                    r = requests.post(f"{HTTP_URL}/api/chargers/{cid}/stop",
                        json={"transaction_id": 1}, timeout=5)
                    print(f"   API Response: {r.json().get('message', r.json())}")
                    c3 = await wait_for_command(ws, "RemoteStopTransaction")
                else:
                    print(f"\n   {YELLOW}Sending RequestStartTransaction via REST API...{RESET}")
                    r = requests.post(f"{HTTP_URL}/api/chargers/{cid}/start",
                        json={"id_tag": "RFID-NEW-USER", "evse_id": 1}, timeout=5)
                    print(f"   API Response: {r.json().get('message', r.json())}")
                    c2 = await wait_for_command(ws, "RequestStartTransaction")

                    print(f"\n   {YELLOW}Sending RequestStopTransaction via REST API...{RESET}")
                    r = requests.post(f"{HTTP_URL}/api/chargers/{cid}/stop",
                        json={"transaction_id": "TX-ABB-001"}, timeout=5)
                    print(f"   API Response: {r.json().get('message', r.json())}")
                    c3 = await wait_for_command(ws, "RequestStopTransaction")

                print(f"\n   {YELLOW}Sending UnlockConnector via REST API...{RESET}")
                r = requests.post(f"{HTTP_URL}/api/chargers/{cid}/unlock",
                    json={"connector_id": 1} if version == "1.6" else {"evse_id": 1, "connector_id": 1}, timeout=5)
                print(f"   API Response: {r.json().get('message', r.json())}")
                c4 = await wait_for_command(ws, "UnlockConnector")

                return all([c1, c2, c3, c4])
            else:
                return True

    except Exception as e:
        print(f"{RED}✘ Exception: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False


async def verify_db():
    """Check database state after tests."""
    import os
    os.environ["DATABASE_URL"] = "sqlite:///local_test.db"
    from shared.db.client import get_db
    from shared.db.models import Charger, ChargingSession, MeterValue, CommandLog
    from sqlalchemy import func

    print(f"\n{'='*70}")
    print(f"{BOLD} DATABASE VERIFICATION{RESET}")
    print(f"{'='*70}")

    with get_db() as db:
        chargers = db.query(Charger).all()
        print(f"\n{BOLD}Chargers ({len(chargers)}):{RESET}")
        for c in chargers:
            print(f"   {c.charger_id:20s}  vendor={c.vendor:10s}  model={c.model:25s}  status={c.status:12s}  ocpp={c.ocpp_version}")

        sessions = db.query(ChargingSession).all()
        print(f"\n{BOLD}Sessions ({len(sessions)}):{RESET}")
        for s in sessions:
            active = "🟢 ACTIVE" if s.stop_time is None else "⚫ CLOSED"
            energy = f"{s.energy_kwh:.1f} kWh" if s.energy_kwh else "N/A"
            print(f"   tx={s.transaction_id:15s}  charger={s.charger_id:20s}  tag={str(s.id_tag):15s}  energy={energy:10s}  {active}")

        meters = db.query(MeterValue).all()
        print(f"\n{BOLD}Meter Values ({len(meters)}):{RESET}")
        for m in meters:
            parts = []
            if m.energy_wh is not None: parts.append(f"energy={m.energy_wh}Wh")
            if m.power_w is not None: parts.append(f"power={m.power_w}W")
            if m.voltage is not None: parts.append(f"voltage={m.voltage}V")
            if m.current_a is not None: parts.append(f"current={m.current_a}A")
            if m.soc is not None: parts.append(f"soc={m.soc}%")
            print(f"   charger={m.charger_id:20s}  {', '.join(parts) if parts else 'no data'}")

        total_energy = db.query(func.sum(ChargingSession.energy_kwh)).scalar() or 0.0
        active_count = db.query(ChargingSession).filter(ChargingSession.stop_time.is_(None)).count()
        cmd_count = db.query(CommandLog).count()

        print(f"\n{BOLD}Dashboard Summary:{RESET}")
        print(f"   Total Energy Delivered: {GREEN}{total_energy:.1f} kWh{RESET}")
        print(f"   Active Sessions:       {GREEN}{active_count}{RESET}")
        print(f"   Commands Sent:         {GREEN}{cmd_count}{RESET}")


async def main():
    print(f"{BOLD}{'='*70}")
    print(f" OCPP REAL-HARDWARE SIMULATION TEST")
    print(f" Simulating ABB Terra AC W22-T-R-0 charger")
    print(f"{'='*70}{RESET}")

    # Health check
    try:
        r = requests.get(f"{HTTP_URL}/api/health", timeout=3)
        print(f"{GREEN}✔ API Server: OK{RESET}")
    except:
        print(f"{RED}✘ API Server not running on port {API_PORT}{RESET}")
        return

    # Test each endpoint
    results = {}
    results["V1.6 Core"] = await test_charger("Core V1.6 (Production)", CORE_PORT, "/ocpp", "ABB-TERRA-V16", "1.6")
    results["V2.0.1 Core"] = await test_charger("Core V2.0.1 (Production)", CORE_PORT, "/ocpp", "ABB-TERRA-V20", "2.0.1")
    results["V1.6 Echo"] = await test_charger("Echo V1.6 (Debug)", ECHO_PORT, "/ocpp-echo", "ABB-ECHO-V16", "1.6")
    results["V2.0.1 Echo-N"] = await test_charger("Echo-N V2.0.1 (Debug)", ECHO_N_PORT, "/ocpp-echo-n", "ABB-ECHO-V20", "2.0.1")

    # Verify DB
    await verify_db()

    # Summary
    print(f"\n{'='*70}")
    print(f"{BOLD} FINAL RESULTS{RESET}")
    print(f"{'='*70}")
    for name, ok in results.items():
        print(f"   {name:20s} {'🟢 PASS' if ok else '🔴 FAIL'}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
