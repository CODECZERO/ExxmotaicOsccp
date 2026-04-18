import asyncio
import requests
import websockets
import sys

# Target Host URL
HOST = "exxomatic.therisewebd.in"
HTTPS_URL = f"https://{HOST}"
WSS_URL = f"wss://{HOST}"

# ANSI Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


def check_api():
    """Test the Flask REST API endpoint."""
    print(f"\n{BOLD}[1] Testing REST API (/api/health)...{RESET}")
    try:
        url = f"{HTTPS_URL}/api/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✔ API is reachable!{RESET} Response: {response.json()}")
            return True
        else:
            print(f"{RED}✘ API failed!{RESET} Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"{RED}✘ API Exception:{RESET} {e}")
        return False


async def check_websocket(name, path, charger_id, version="1.6"):
    """Test connection to an OCPP WebSocket endpoint and send mock data."""
    import json
    print(f"\n{BOLD}[*] Testing {name} ({path}) [Version {version}]...{RESET}")
    url = f"{WSS_URL}{path}/{version}/{charger_id}"
    
    try:
        subprotocol = "ocpp1.6" if version == "1.6" else "ocpp2.0.1"
        async with websockets.connect(url, subprotocols=[subprotocol], open_timeout=5) as ws:
            print(f"{GREEN}✔ {name} connection established!{RESET}")
            
            # 1. Send BootNotification
            print(f"   -> Sending BootNotification...")
            if version == "1.6":
                boot_msg = [2, "msg-boot", "BootNotification", {"chargePointVendor": "DiagBot", "chargePointModel": "RemoteTest"}]
            else:
                boot_msg = [2, "msg-boot", "BootNotification", {"chargingStation": {"vendorName": "DiagBot", "model": "RemoteTest-201"}, "reason": "PowerUp"}]
                
            await ws.send(json.dumps(boot_msg))
            try:
                resp1 = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"   <- Received: {resp1[:80]}...")
            except asyncio.TimeoutError:
                print(f"   <- Waiting for ACK... (Continuing)")
            
            # 2. Send Heartbeat
            print(f"   -> Sending Heartbeat...")
            heart_msg = [2, "msg-heart", "Heartbeat", {}]
            await ws.send(json.dumps(heart_msg))
            try:
                resp2 = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"   <- Received: {resp2[:80]}...")
            except asyncio.TimeoutError:
                print(f"   <- Waiting for ACK... (Continuing)")
            
            print(f"{GREEN}✔ {name} successfully transmitted payload!{RESET}")
            return True
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"{RED}✘ {name} rejected connection!{RESET} Status code: {e.status_code}")
        if e.status_code == 404:
            print(f"   (Hint: Check if HAProxy is routing {path} correctly)")
        return False
    except asyncio.TimeoutError:
        print(f"{RED}✘ {name} timed out waiting for response!{RESET}")
        return False
    except Exception as e:
        print(f"{RED}✘ {name} Exception:{RESET} {e}")
        return False


async def test_all():
    print(f"=== Starting Diagnosic Tests for {HOST} ===")
    
    # 1. API Check
    api_ok = check_api()
    
    # 2. WebSocket Checks
    print(f"\n{BOLD}--- Testing WebSocket Endpoints ---{RESET}")
    charger_id = "DIAGNOSTIC_BOT"
    
    core_ok = await check_websocket("Production OCPP Core", "/ocpp", charger_id, version="1.6")
    echo_ok = await check_websocket("OCPP Echo Server", "/ocpp-echo", charger_id, version="1.6")
    echo_n_ok = await check_websocket("OCPP Echo-N Server", "/ocpp-echo-n", charger_id, version="2.0.1")
    
    # 3. Validation Check
    print(f"\n{BOLD}[3] Verifying Database Persistence (/api/chargers)...{RESET}")
    db_ok = False
    try:
        url = f"{HTTPS_URL}/api/chargers/{charger_id}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            charger = resp.json().get('charger', {})
            print(f"{GREEN}✔ Database integration confirmed!{RESET} Found: {charger.get('charger_id')} (Status: {charger.get('status')})")
            db_ok = True
        else:
            print(f"{RED}✘ Persistence failed!{RESET} API returned: {resp.status_code}")
    except Exception as e:
        print(f"{RED}✘ Persistence Check Exception:{RESET} {e}")

    print(f"\n{BOLD}=== Test Summary ==={RESET}")
    print(f"REST API:     {'🟢 PASS' if api_ok else '🔴 FAIL'}")
    print(f"Core Server:  {'🟢 PASS' if core_ok else '🔴 FAIL'}")
    print(f"Echo Server:  {'🟢 PASS' if echo_ok else '🔴 FAIL'}")
    print(f"Echo-N Server:{'🟢 PASS' if echo_n_ok else '🔴 FAIL'}")
    print(f"DB Tracking:  {'🟢 PASS' if db_ok else '🔴 FAIL'}")

if __name__ == "__main__":
    asyncio.run(test_all())
