import sys
import os

# Add the root project directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.db.client import get_db, engine
from shared.db.models import Charger, ChargingSession, MeterValue, CommandLog
from sqlalchemy import text

print("Clearing all data from the database...")

with get_db() as db:
    try:
        # Delete all records
        db.query(MeterValue).delete()
        db.query(CommandLog).delete()
        db.query(ChargingSession).delete()
        db.query(Charger).delete()
        
        # Commit changes
        db.commit()
        print("Successfully deleted all fake data from the database!")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
