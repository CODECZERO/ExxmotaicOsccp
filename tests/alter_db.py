import os
import sys

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.env import load_env
load_env()

from shared.db.client import engine

def alter_db():
    if engine is None:
        print("Error: DATABASE_URL not set in environment.")
        return
    
    print(f"Altering database: {os.getenv('DATABASE_URL').split('@')[-1]}")
    try:
        # Connect explicitly to run an ALTER command directly
        with engine.begin() as conn:
            from sqlalchemy import text
            # PostgreSQL syntax to alter column length and ignore errors if it wasn't a varchar
            # This expands the column to 255 chars to prevent StringDataRightTruncation
            conn.execute(text("ALTER TABLE command_logs ALTER COLUMN status TYPE VARCHAR(255);"))
        print("Successfully updated command_logs.status to VARCHAR(255).")
    except Exception as e:
        print(f"Error altering tables (it might already be applied or you're using sqlite): {e}")

if __name__ == "__main__":
    alter_db()
