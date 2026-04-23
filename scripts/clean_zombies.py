import sys
import os
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.env import load_env
load_env()

from shared.db.client import get_db, db_available
from shared.db.models import ChargingSession

def clean_zombies():
    if not db_available():
        print("No database configured.")
        return

    print("Cleaning up old zombie sessions...")
    try:
        with get_db() as db:
            zombies = db.query(ChargingSession).filter(ChargingSession.stop_time.is_(None)).all()
            count = 0
            for z in zombies:
                z.stop_time = datetime.now(tz=timezone.utc)
                count += 1
            print(f"✅ Successfully closed {count} zombie sessions.")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    clean_zombies()
