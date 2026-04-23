import asyncio
import logging
import websockets
import os
import sys
import time
import uuid
import random
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.routing import on
from ocpp.v16 import call, call_result
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RemoteStartStopStatus

# Configure logging (set to WARNING to reduce noise from the ocpp library)
logging.basicConfig(level=logging.WARNING)

SERVER_URL = "wss://exxocharger.exxomatic.in/ocpp"

class SmartFakeCharger(cp):
    def __init__(self, id, connection):
        super().__init__(id, connection)
        self.transaction_id = None
        self.meter_value = 0
        self.is_charging = False

    # ─── Commands received FROM the server (Remote Control) ─────────────────
    
    @on(Action.remote_start_transaction)
    async def on_remote_start_transaction(self, id_tag, **kwargs):
        print(f"[{self.id}] 📱 Received RemoteStartTransaction from Dashboard (Tag: {id_tag})")
        
        if self.is_charging:
            print(f"[{self.id}] ⚠️ Already charging, rejecting start.")
            return call_result.RemoteStartTransaction(status=RemoteStartStopStatus.rejected)

        # Accept the remote start
        print(f"[{self.id}] ✅ Accepted RemoteStartTransaction. Beginning charge...")
        
        # In a real charger, we'd wait a moment and then send a StartTransaction.
        # We can trigger that via an asyncio task so we don't block this response.
        asyncio.create_task(self.delayed_start_transaction(id_tag))
        
        return call_result.RemoteStartTransaction(status=RemoteStartStopStatus.accepted)

    @on(Action.remote_stop_transaction)
    async def on_remote_stop_transaction(self, transaction_id, **kwargs):
        print(f"[{self.id}] 🛑 Received RemoteStopTransaction from Dashboard (Tx: {transaction_id})")
        
        if not self.is_charging or transaction_id != self.transaction_id:
            return call_result.RemoteStopTransaction(status=RemoteStartStopStatus.rejected)

        print(f"[{self.id}] ✅ Accepted RemoteStopTransaction. Ending charge...")
        
        # Trigger StopTransaction in the background
        asyncio.create_task(self.delayed_stop_transaction())
        
        return call_result.RemoteStopTransaction(status=RemoteStartStopStatus.accepted)

    # ─── Internal logic to simulate hardware actions ────────────────────────

    async def delayed_start_transaction(self, id_tag: str):
        await asyncio.sleep(2)
        print(f"[{self.id}] 🚀 Sending StartTransaction to Server...")
        request = call.StartTransaction(
            connector_id=1,
            id_tag=id_tag,
            meter_start=self.meter_value,
            timestamp=datetime.now(tz=timezone.utc).isoformat()
        )
        response = await self.call(request)
        if response.id_tag_info.get("status") == "Accepted":
            self.transaction_id = response.transaction_id
            self.is_charging = True
            print(f"[{self.id}] 🔌 Transaction {self.transaction_id} Started Successfully!")

    async def delayed_stop_transaction(self):
        await asyncio.sleep(2)
        print(f"[{self.id}] 📉 Sending StopTransaction to Server...")
        request = call.StopTransaction(
            meter_stop=self.meter_value,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            transaction_id=self.transaction_id
        )
        await self.call(request)
        self.is_charging = False
        self.transaction_id = None
        print(f"[{self.id}] 🔌 Transaction Stopped.")

    async def send_boot_notification(self):
        print(f"[{self.id}] 📡 Sending BootNotification...")
        request = call.BootNotification(
            charge_point_model="Smart-Sim-60kW",
            charge_point_vendor="Exxomatic Test"
        )
        await self.call(request)

    async def send_heartbeat(self):
        request = call.Heartbeat()
        await self.call(request)

    async def send_meter_values(self):
        if not self.is_charging or not self.transaction_id:
            return

        self.meter_value += random.randint(150, 300)
        print(f"[{self.id}] ⚡ Streaming Data: {self.meter_value} Wh")
        
        request = call.MeterValues(
            connector_id=1,
            transaction_id=self.transaction_id,
            meter_value=[
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "sampled_value": [
                        {
                            "value": str(self.meter_value),
                            "context": "Sample.Periodic",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "Wh"
                        }
                    ]
                }
            ]
        )
        await self.call(request)

async def simulate_smart_charger(charger_id: str):
    uri = f"{SERVER_URL}/1.6/{charger_id}"
    print(f"🔌 Connecting {charger_id} to {uri}...")
    
    try:
        async with websockets.connect(uri, subprotocols=['ocpp1.6']) as ws:
            print(f"✅ {charger_id} Connected!")
            
            charger = SmartFakeCharger(charger_id, ws)

            # Boot immediately
            await charger.send_boot_notification()

            # Start the background data loop
            async def background_loop():
                counter = 0
                while True:
                    await asyncio.sleep(2)  # Stream very quickly for the test
                    counter += 1
                    
                    if charger.is_charging:
                        await charger.send_meter_values()
                    
                    if counter % 10 == 0:
                        await charger.send_heartbeat()

            # Run both the OCPP listener and the background loop concurrently
            await asyncio.gather(
                charger.start(),
                background_loop()
            )
            
    except Exception as e:
        print(f"❌ Connection Failed for {charger_id}: {e}")

async def main():
    print("=========================================================")
    print("  Smart Load Test — Bi-Directional WSS OCPP Simulator  ")
    print("=========================================================\n")
    print("These chargers are now listening for RemoteStart commands from the Dashboard!\n")
    
    await asyncio.gather(
        simulate_smart_charger("SMART_TEST_1"),
        simulate_smart_charger("SMART_TEST_2")
    )

if __name__ == '__main__':
    asyncio.run(main())
