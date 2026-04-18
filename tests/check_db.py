import sys
import os
os.environ["DATABASE_URL"] = "sqlite:///local_test.db"

from shared.db.client import get_db, db_available
from shared.db.models import Charger, ChargingSession, MeterValue, CommandLog
from sqlalchemy import func

def check():
    print("Database Available:", db_available())
    with get_db() as db:
        chargers = db.query(Charger).count()
        print(f"Total Chargers: {chargers}")
        
        sessions = db.query(ChargingSession).count()
        active = db.query(ChargingSession).filter(ChargingSession.stop_time == None).count()
        print(f"Total Sessions: {sessions} (Active: {active})")
        
        meters = db.query(MeterValue).count()
        print(f"Total MeterValues: {meters}")
        
        cmds = db.query(CommandLog).count()
        print(f"Total Commands: {cmds}")
        
        energy = db.query(func.sum(ChargingSession.energy_kwh)).scalar() or 0.0
        print(f"Total Energy kWh: {energy}")

if __name__ == '__main__':
    check()
