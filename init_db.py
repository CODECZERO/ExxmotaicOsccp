import os
import sys

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.env import load_env
load_env()

from shared.db.client import engine
from shared.db.models import Base

def init_db():
    if engine is None:
        print("Error: DATABASE_URL not set in environment.")
        return
    
    print(f"Initializing database: {os.getenv('DATABASE_URL').split('@')[-1]}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Successfully created all tables.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
