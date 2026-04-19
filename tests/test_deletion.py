import os
import sys

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.env import load_env
load_env()

# Trick it into using a fresh local DB
os.environ["DATABASE_URL"] = "sqlite:///deletion_test.db"

from shared.db.client import engine, get_db
from shared.db.models import Base, Charger, ChargingSession, MeterValue, CommandLog
from api.controllers import charger_controller

def setup_db():
    print("--- Setting up clean test DB ---")
    if os.path.exists("deletion_test.db"):
        os.remove("deletion_test.db")
    Base.metadata.create_all(bind=engine)
    print("DB initialized.")

def run_test():
    setup_db()
    
    charger_id = "TEST-CHARGER-001"
    
    print("\n1. Registering charger...")
    res, status = charger_controller.create({"charger_id": charger_id, "vendor": "Test", "model": "TestModel"})
    assert status == 201, f"Failed to create charger: {res}"
    print("✔ Charger created.")
    
    print("\n2. Adding associated data (sessions, meter values, logs)...")
    with get_db() as db:
        # Add a session
        session = ChargingSession(
            charger_id=charger_id,
            transaction_id="TX-001",
            id_tag="RFID-1",
            start_time=datetime.now()
        )
        db.add(session)
        db.flush()
        
        # Add meter value for session
        mv = MeterValue(
            charger_id=charger_id,
            session_id=session.id,
            timestamp=datetime.now(),
            energy_wh=100.0
        )
        db.add(mv)
        
        # Add orphan meter value (not linked to session, but linked to charger)
        mv2 = MeterValue(
            charger_id=charger_id,
            timestamp=datetime.now(),
            energy_wh=50.0
        )
        db.add(mv2)
        
        # Add a command log
        cmd = CommandLog(
            charger_id=charger_id,
            command="Reset",
            status="Pending"
        )
        db.add(cmd)
        
        db.commit()
    print("✔ Data added.")
    
    # Verify counts before deletion
    with get_db() as db:
        assert db.query(Charger).count() == 1
        assert db.query(ChargingSession).count() == 1
        assert db.query(MeterValue).count() == 2
        assert db.query(CommandLog).count() == 1
    print("✔ Initial counts verified.")
    
    print("\n3. Deleting charger via controller...")
    res, status = charger_controller.delete(charger_id)
    assert status == 200, f"Deletion failed: {res}"
    print(f"✔ Controller returned: {res['message']}")
    
    print("\n4. Verifying cascading cleanup...")
    with get_db() as db:
        c_count = db.query(Charger).count()
        s_count = db.query(ChargingSession).count()
        m_count = db.query(MeterValue).count()
        l_count = db.query(CommandLog).count()
        
        print(f"Chargers: {c_count}")
        print(f"Sessions: {s_count}")
        print(f"MeterValues: {m_count}")
        print(f"CommandLogs: {l_count}")
        
        assert c_count == 0, "Charger was not deleted!"
        assert s_count == 0, "Sessions were not cleaned up!"
        assert m_count == 0, "MeterValues were not cleaned up!"
        assert l_count == 0, "CommandLogs were not cleaned up!"
        
    print("\n🎉 ALL TESTS PASSED! Cascading deletion is working perfectly.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if os.path.exists("deletion_test.db"):
            os.remove("deletion_test.db")
