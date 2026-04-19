import asyncio
import websockets
import json
import uuid
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Configuration ────────────────────────────────────────────────────────
# Change to "wss://" if you enable Cloudflare "Strict" SSL. "ws://" works for Flexible.
SERVER_URL = "wss://exxomatic.therisewebd.in/ocpp"

async def simulate_ocpp16_charger(charger_id: str):
    """Simulates an OCPP 1.6J Charger"""
    url = f"{SERVER_URL}/1.6/{charger_id}"
    print(f"[V1.6] 🔌 Connecting to {url}...")
    
    try:
        # Connect using the specific subprotocol
        async with websockets.connect(url, subprotocols=["ocpp1.6"]) as ws:
            print(f"[V1.6] ✅ Connected!")
            
            # 1. Send BootNotification
            msg_id = str(uuid.uuid4())
            boot_msg = [
                2, msg_id, "BootNotification",
                {
                    "chargePointModel": "Model-16J-Pro",
                    "chargePointVendor": "TestVendor"
                }
            ]
            print(f"[V1.6] 📨 Sending BootNotification...")
            await ws.send(json.dumps(boot_msg))
            
            # Wait for response
            response = await ws.recv()
            print(f"[V1.6] 📩 Server Response: {response}")
            
            # 2. Send Heartbeat
            msg_id = str(uuid.uuid4())
            heartbeat_msg = [2, msg_id, "Heartbeat", {}]
            print(f"[V1.6] 💓 Sending Heartbeat...")
            await ws.send(json.dumps(heartbeat_msg))
            response = await ws.recv()
            print(f"[V1.6] 📩 Server Response: {response}")
            
            print(f"[V1.6] ✨ V1.6 Test Complete!\n")
            
    except Exception as e:
        print(f"[V1.6] ❌ Connection Failed: {e}\n")


async def simulate_ocpp201_charger(charger_id: str):
    """Simulates an OCPP 2.0.1 Charger"""
    url = f"{SERVER_URL}/2.0.1/{charger_id}"
    print(f"[V2.0.1] 🔌 Connecting to {url}...")
    
    try:
        # Connect using the specific subprotocol
        async with websockets.connect(url, subprotocols=["ocpp2.0.1"]) as ws:
            print(f"[V2.0.1] ✅ Connected!")
            
            # 1. Send BootNotification (V20 format is different!)
            msg_id = str(uuid.uuid4())
            boot_msg = [
                2, msg_id, "BootNotification",
                {
                    "reason": "PowerUp",
                    "chargingStation": {
                        "model": "Model-20-Ultra",
                        "vendorName": "FutureTech"
                    }
                }
            ]
            print(f"[V2.0.1] 📨 Sending BootNotification...")
            await ws.send(json.dumps(boot_msg))
            
            # Wait for response
            response = await ws.recv()
            print(f"[V2.0.1] 📩 Server Response: {response}")
            
            print(f"[V2.0.1] ✨ V2.0.1 Test Complete!\n")
            
    except Exception as e:
        print(f"[V2.0.1] ❌ Connection Failed: {e}\n")

async def main():
    print("==================================================")
    print("  Exxomatic Live Server Health & Data Injector  ")
    print("==================================================\n")
    
    # Run the 1.6 simulation
    await simulate_ocpp16_charger("TEST_CP_16")
    
    # Wait a second to allow DB settling
    await asyncio.sleep(2)
    
    # Run the 2.0.1 simulation
    await simulate_ocpp201_charger("TEST_CP_20")
    
    print("==================================================")
    print("All injections complete! Go check your Next.js Dashboard to see the chargers!")

if __name__ == "__main__":
    asyncio.run(main())
