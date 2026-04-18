"""Cleanup stale Pending commands from the database.

Run this ONCE on the production server to clear accumulated garbage:
    python cleanup_stale_commands.py

After running, the new dispatcher with TTL-based auto-expiry will prevent
stale commands from accumulating again.
"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.env import load_env
load_env()

from shared.db.client import get_db, db_available
from shared.db.models import CommandLog


def cleanup():
    if not db_available():
        print("ERROR: DATABASE_URL not set")
        return

    with get_db() as db:
        if db is None:
            print("ERROR: Could not open DB session")
            return

        stale = db.query(CommandLog).filter(CommandLog.status == "Pending").all()
        count = len(stale)

        if count == 0:
            print("No stale Pending commands found. DB is clean.")
            return

        print(f"Found {count} stale Pending commands:")
        for cmd in stale:
            print(f"  #{cmd.id}  charger={cmd.charger_id}  cmd={cmd.command}  created={cmd.created_at}")
            cmd.status = "Expired"

        db.commit()
        print(f"\n✔ Marked {count} commands as 'Expired'. DB is clean.")


if __name__ == "__main__":
    cleanup()
