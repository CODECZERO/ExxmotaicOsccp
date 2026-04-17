import asyncio
import logging
import websockets
from datetime import datetime

from ocpp.v16 import call
from ocpp.v16 import ChargePoint as cp

logging.basicConfig(level=logging.INFO)

class FakeCharger(cp):
    async def send_boot_notification(self):
        print("Sending BootNotification...")
        request = call.BootNotification(
            charge_point_model="DC-60kW",
            charge_point_vendor="TKT"
        )
        response = await self.call(request)
        print(f"BootNotification response: {response.status}")

    async def send_heartbeat(self):
        print("Sending Heartbeat...")
        request = call.Heartbeat()
        response = await self.call(request)
        print(f"Heartbeat response timestamp: {response.current_time}")

    async def send_meter_values(self, energy_wh):
        print(f"Sending MeterValues ({energy_wh} Wh)...")
        request = call.MeterValues(
            connector_id=1,
            meter_value=[
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "sampled_value": [
                        {
                            "value": str(energy_wh),
                            "context": "Sample.Periodic",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "Wh"
                        }
                    ]
                }
            ]
        )
        await self.call(request)
        print(f"MeterValues sent!")

async def main():
    # Connecting to the Core WebSocket server using the demo charger ID
    uri = 'ws://localhost:5000/ocpp/1.6/DEMO-DC-001'
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(
        uri,
        subprotocols=['ocpp1.6']
    ) as ws:

        charger = FakeCharger('DEMO-DC-001', ws)

        # Run the charger instance and the async tasks loop
        await asyncio.gather(charger.start(), background_tasks(charger))

async def background_tasks(charger):
    await asyncio.sleep(2)
    await charger.send_boot_notification()
    
    energy_wh = 12000
    while True:
        await asyncio.sleep(5)
        await charger.send_heartbeat()
        await asyncio.sleep(5)
        energy_wh += random.randint(100, 500)
        await charger.send_meter_values(energy_wh)

if __name__ == '__main__':
    asyncio.run(main())
