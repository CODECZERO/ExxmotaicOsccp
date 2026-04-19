import asyncio
import requests
import websockets
import json
import sys
import os
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Target Host URL
HOST = "exxomatic.therisewebd.in"
HTTPS_URL = f"https://{HOST}"
WSS_URL = f"wss://{HOST}"

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'


async def drain_buffer(ws, timeout=0.5):
    """Read and discard all buffered messages (CallResults from data payloads)."""
    count = 0
    while True:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            parsed = json.loads(msg)
            if isinstance(parsed, list) and parsed[0] == 3:
                # Show server response status
                print(f"   {DIM}<- Response [{parsed[1]}]: {json.dumps(parsed[2]) if len(parsed) > 2 else '{}'}{RESET}")
            count += 1
        except asyncio.TimeoutError:
            break
    return count


async def wait_for_command(ws, expected_cmd):
    try:
        # Loop to ignore delayed CallResult [3, ...] or stale commands
        for _ in range(20):
            msg = await asyncio.wait_for(ws.recv(), timeout=15)
            parsed = json.loads(msg)
            
            if not isinstance(parsed, list):
                continue

            # Skip CallResults (heartbeat/meter/status acknowledgements)
            if parsed[0] == 3:
                continue
            
            # It's a Call [2, id, action, payload]
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
                    # Stale command from a previous run. Ack it and continue.
                    print(f"   {YELLOW}  (stale — acking){RESET}")
                    await ws.send(json.dumps([3, msg_id, {"status": "Accepted"}]))
                    continue
                    
        print(f"{RED}   ✘ FAILED: Exceeded max buffered responses waiting for {expected_cmd}{RESET}")
        return False
    except asyncio.timeout:
        print(f"{RED}   ✘ FAILED: Timeout waiting for {expected_cmd}. Is Poller running?{RESET}")
        return False
    except asyncio.TimeoutError:
        print(f"{RED}   ✘ FAILED: Timeout waiting for {expected_cmd}. Is Poller running?{RESET}")
        return False


async def test_all():
    print(f"{BOLD}{'='*70}")
    print(f" EXXOMATIC PRODUCTION DIAGNOSTIC — {HOST}")
    print(f"{'='*70}{RESET}")
    
    # 1. API Health
    api_ok = False
    try:
        r = requests.get(f"{HTTPS_URL}/api/health", timeout=10)
        print(f"{GREEN}✔ API Healthy: {r.json()}{RESET}")
        api_ok = True
    except Exception as e:
        print(f"{RED}✘ API Down: {e}{RESET}")

    # 2. Version Restriction Tests
    print(f"\n{BOLD}── TESTING VERSION RESTRICTION LOGIC ──{RESET}")
    async def try_connect(path, ver):
        try:
            async with websockets.connect(f"{WSS_URL}{path}/{ver}/REJ_T", subprotocols=[f"ocpp{ver}"], open_timeout=5) as ws:
                return False # Should have rejected!
        except (websockets.exceptions.InvalidStatus, websockets.exceptions.InvalidHandshake, TimeoutError, asyncio.TimeoutError):
            return True # Correctly rejected or dropped
    
    re_ok = await try_connect("/ocpp-echo", "2.0.1")
    ren_ok = await try_connect("/ocpp-echo-n", "1.6")
    print(f"{GREEN}✔ Restrictions active (Both Echo and Echo-N caught bad endpoints){RESET}" if (re_ok and ren_ok) else f"{RED}✘ Restriction bypass detected{RESET}")

    # 3. Functional Tests - Real Sockets
    print(f"\n{BOLD}── TESTING PRODUCTION DATA FLOW & COMMANDS ──{RESET}")

    async def test_charger(name, path, cid, version):
        print(f"\n{BOLD}[*] Testing {name} [Version {version}]...{RESET}")
        print(f"    Path: {path}/{version}/{cid}")
        cmd_ok = False
        try:
            url = f"{WSS_URL}{path}/{version}/{cid}"
            sub = "ocpp1.6" if version == "1.6" else "ocpp2.0.1"
            async with websockets.connect(url, subprotocols=[sub], open_timeout=15) as ws:
                print(f"{GREEN}✔ Connected!{RESET}")
                
                # === PHASE 1: Send all data payloads ===
                ts = datetime.now(tz=timezone.utc).isoformat()
                if version == "1.6":
                    # Boot
                    await ws.send(json.dumps([2, "mb", "BootNotification", {"chargePointVendor": "Diag", "chargePointModel": "RM-SIM"}]))
                    await asyncio.wait_for(ws.recv(), timeout=10)
                    # Status
                    await ws.send(json.dumps([2, "ms", "StatusNotification", {"connectorId": 1, "errorCode": "NoError", "status": "Charging"}]))
                    # Start
                    await ws.send(json.dumps([2, "st", "StartTransaction", {"connectorId": 1, "idTag": "REMOTE123", "meterStart": 5000, "timestamp": ts}]))
                    # Meter
                    await ws.send(json.dumps([2, "mm", "MeterValues", {"connectorId": 1, "transactionId": 1, "meterValue": [{"timestamp": ts, "sampledValue": [{"value": "8200", "unit": "Wh", "measurand": "Energy.Active.Import.Register"}]}]}]))
                    # Heartbeat
                    await ws.send(json.dumps([2, "mh", "Heartbeat", {}]))
                else:
                    # Boot
                    await ws.send(json.dumps([2, "mb", "BootNotification", {"chargingStation": {"vendorName": "Diag", "model": "RM-SIM-V2"}, "reason": "PowerUp"}]))
                    await asyncio.wait_for(ws.recv(), timeout=10)
                    # Status
                    await ws.send(json.dumps([2, "ms", "StatusNotification", {"timestamp": ts, "connectorStatus": "Occupied", "evseId": 1, "connectorId": 1}]))
                    # Start
                    await ws.send(json.dumps([2, "st", "TransactionEvent", {"eventType": "Started", "timestamp": ts, "triggerReason": "Authorized", "seqNo": 1, "transactionInfo": {"transactionId": "TX-REMOTE-201"}}]))
                    # Meter
                    await ws.send(json.dumps([2, "mm", "MeterValues", {"evseId": 1, "meterValue": [{"timestamp": ts, "sampledValue": [{"value": 8200.0, "measurand": "Energy.Active.Import.Register"}]}]}]))
                    # End
                    await ws.send(json.dumps([2, "end", "TransactionEvent", {"eventType": "Ended", "timestamp": ts, "triggerReason": "StopAuthorized", "seqNo": 2, "transactionInfo": {"transactionId": "TX-REMOTE-201"}, "meterValue": [{"timestamp": ts, "sampledValue": [{"value": 15000.0, "measurand": "Energy.Active.Import.Register"}]}]}]))
                    # Heartbeat
                    await ws.send(json.dumps([2, "mh", "Heartbeat", {}]))

                # === PHASE 2: Drain ALL buffered responses ===
                # Wait 5s for the production server to process all messages (especially on DB inserts)
                print(f"    (Waiting 5s for DB processing...)")
                await asyncio.sleep(5)
                drained = await drain_buffer(ws, timeout=2.0)
                print(f"    {GREEN}✔ Payload Transmission Complete! (drained {drained} responses){RESET}")

                # === PHASE 3: Command delivery test (Core only) ===
                if path == "/ocpp":
                    print(f"    {BOLD}── TESTING COMMAND DELIVERY ──{RESET}")
                    
                    # Reset
                    print(f"   {YELLOW}-> Sending Reset via API...{RESET}")
                    requests.post(f"{HTTPS_URL}/api/chargers/{cid}/reset", json={"type": "Soft" if version == "1.6" else "OnIdle"}, timeout=10)
                    c1 = await wait_for_command(ws, "Reset")
                    
                    # Start/Stop
                    if version == "1.6":
                        print(f"   {YELLOW}-> Sending RemoteStart via API...{RESET}")
                        requests.post(f"{HTTPS_URL}/api/chargers/{cid}/start", json={"id_tag": "REMOTE_U", "connector_id": 1}, timeout=10)
                        c2 = await wait_for_command(ws, "RemoteStartTransaction")
                        
                        print(f"   {YELLOW}-> Sending RemoteStop via API...{RESET}")
                        requests.post(f"{HTTPS_URL}/api/chargers/{cid}/stop", json={"transaction_id": 9999}, timeout=10)
                        c3 = await wait_for_command(ws, "RemoteStopTransaction")
                    else:
                        print(f"   {YELLOW}-> Sending RequestStart via API...{RESET}")
                        requests.post(f"{HTTPS_URL}/api/chargers/{cid}/start", json={"id_tag": "REMOTE_U", "evse_id": 1}, timeout=10)
                        c2 = await wait_for_command(ws, "RequestStartTransaction")
                        
                        print(f"   {YELLOW}-> Sending RequestStop via API...{RESET}")
                        requests.post(f"{HTTPS_URL}/api/chargers/{cid}/stop", json={"transaction_id": "TX-REMOTE-201"}, timeout=10)
                        c3 = await wait_for_command(ws, "RequestStopTransaction")
                    
                    # Unlock
                    print(f"   {YELLOW}-> Sending Unlock via API...{RESET}")
                    requests.post(f"{HTTPS_URL}/api/chargers/{cid}/unlock", json={"connector_id": 1} if version == "1.6" else {"evse_id": 1, "connector_id": 1}, timeout=10)
                    c4 = await wait_for_command(ws, "UnlockConnector")
                    
                    cmd_ok = all([c1, c2, c3, c4])
                else:
                    cmd_ok = True

                return cmd_ok
        except Exception as e:
            print(f"{RED}✘ Exception: {e}{RESET}")
            return False

    v16_core = await test_charger("Production Core V1.6", "/ocpp", "R_BOT_V16", "1.6")
    v20_core = await test_charger("Production Core V2.0.1", "/ocpp", "R_BOT_V20", "2.0.1")
    v16_echo = await test_charger("Echo Server V1.6", "/ocpp-echo", "R_ECHO_V16", "1.6")
    v20_echon = await test_charger("Echo-N Server V2", "/ocpp-echo-n", "R_ECHO_V20", "2.0.1")

    print(f"\n{BOLD}=== FINAL PRODUCTION SUMMARY ==={RESET}")
    print(f"REST API:      {'🟢 PASS' if api_ok else '🔴 FAIL'}")
    print(f"V1.6 Core:     {'🟢 PASS' if v16_core else '🔴 FAIL'}")
    print(f"V2.0.1 Core:   {'🟢 PASS' if v20_core else '🔴 FAIL'}")
    print(f"V1.6 Echo:     {'🟢 PASS' if v16_echo else '🔴 FAIL'}")
    print(f"V2.0.1 Echo-N: {'🟢 PASS' if v20_echon else '🔴 FAIL'}")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(test_all())
