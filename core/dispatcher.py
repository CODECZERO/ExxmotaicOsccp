"""core.dispatcher — Connection registry and command polling logic."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from shared.db.client import get_db, db_available
from shared.db.models import CommandLog
from core.V16.charge_point import V16ChargePoint
from core.V20.charge_point import V201ChargePoint

logger = logging.getLogger(__name__)

# Registry of active chargers connected to THIS process
# Key: charger_id (str), Value: ChargePoint instance
active_connections: Dict[str, Any] = {}

# How long a "Pending" command stays valid before being auto-expired
COMMAND_TTL_SECONDS = 30

# Per-dispatch timeout — prevents a single stuck command from blocking the poller
DISPATCH_TIMEOUT_SECONDS = 10


def _fetch_pending_commands(active_ids: list[str]) -> list[dict]:
    """Fetch pending commands from DB, expiring stale ones."""
    if not active_ids or not db_available():
        return []
    
    try:
        with get_db() as db:
            if db is None:
                return []
            
            # 1. Expire stale pending commands
            cutoff = datetime.now(tz=timezone.utc) - timedelta(seconds=COMMAND_TTL_SECONDS)
            stale = (
                db.query(CommandLog)
                .filter(CommandLog.status == "Pending")
                .filter(CommandLog.created_at < cutoff)
                .all()
            )
            for cmd in stale:
                cmd.status = "Expired"
                logger.info("Expired stale command %s (#%s)", cmd.command, cmd.id)
            if stale:
                db.commit()

            # 2. Find pending commands for active chargers
            pending = (
                db.query(CommandLog)
                .filter(CommandLog.status == "Pending")
                .filter(CommandLog.charger_id.in_(active_ids))
                .order_by(CommandLog.created_at.asc())
                .all()
            )
            
            return [
                {
                    "id": cmd.id,
                    "charger_id": cmd.charger_id,
                    "command": cmd.command,
                    "payload": cmd.payload,
                }
                for cmd in pending
            ]
    except Exception:
        logger.exception("Error fetching commands")
        return []


def _update_command_status(cmd_id: int, status: str):
    """Update command status in DB."""
    try:
        with get_db() as db:
            if db is None: return
            cmd = db.query(CommandLog).filter(CommandLog.id == cmd_id).first()
            if cmd:
                cmd.status = status
                db.commit()
    except Exception:
        logger.exception("Error updating command status")


async def start_command_poller(interval: float = 1.0):
    """
    Background loop that polls the DB for 'Pending' commands for ANY charger
    currently connected to this specific process.
    """
    logger.info("Starting CommandPoller loop (interval=%.1fs)", interval)
    
    while True:
        try:
            active_ids = list(active_connections.keys())
            if not active_ids or not db_available():
                await asyncio.sleep(interval)
                continue
                
            # Fetch pending commands in a background thread to prevent blocking the asyncio loop!
            pending_cmds = await asyncio.to_thread(_fetch_pending_commands, active_ids)
            
            for cmd in pending_cmds:
                try:
                    # Dispatch to charger asynchronously (DB connection is NOT held here)
                    status = await asyncio.wait_for(
                        _dispatch_command_dict(cmd),
                        timeout=DISPATCH_TIMEOUT_SECONDS,
                    )
                    # Update status in background thread
                    await asyncio.to_thread(_update_command_status, cmd["id"], status)
                except asyncio.TimeoutError:
                    logger.warning("Dispatch timeout for %s", cmd["charger_id"])
                    await asyncio.to_thread(_update_command_status, cmd["id"], f"Error: Dispatch timeout ({DISPATCH_TIMEOUT_SECONDS}s)")
                except Exception as e:
                    logger.exception("Dispatch error")
                    await asyncio.to_thread(_update_command_status, cmd["id"], f"Error: {str(e)[:250]}")
                    
        except Exception:
            logger.exception("Error in CommandPoller loop")
            
        await asyncio.sleep(interval)


async def _dispatch_command_dict(cmd: dict) -> str:
    """Attempt to send the command to the physical charger via its active socket."""
    charger_id = cmd["charger_id"]
    cp = active_connections.get(charger_id)
    
    if not cp:
        return "Failed"

    logger.info("Dispatching command %s to charger %s", cmd["command"], charger_id)
    
    status = "Failed"
    payload = cmd["payload"] or {}
    command = cmd["command"]
    
    if isinstance(cp, V16ChargePoint):
        if command == "RemoteStartTransaction":
            status = await cp.remote_start(
                id_tag=payload.get("id_tag", "UNKNOWN"),
                connector_id=payload.get("connector_id", 1)
            )
        elif command == "RemoteStopTransaction":
            status = await cp.remote_stop(
                transaction_id=int(payload.get("transaction_id", 0))
            )
        elif command == "Reset":
            status = await cp.reset(reset_type=payload.get("type", "Soft"))
        elif command == "UnlockConnector":
            status = await cp.unlock(connector_id=payload.get("connector_id", 1))
            
    elif isinstance(cp, V201ChargePoint):
        if command == "RemoteStartTransaction":
            status = await cp.request_start(
                id_tag=payload.get("id_tag", "UNKNOWN"),
                evse_id=payload.get("evse_id", 1)
            )
        elif command == "RemoteStopTransaction":
            status = await cp.request_stop(
                transaction_id=str(payload.get("transaction_id", ""))
            )
        elif command == "Reset":
            status = await cp.reset(reset_type=payload.get("type", "OnIdle"))
        elif command == "UnlockConnector":
            status = await cp.unlock(
                evse_id=payload.get("evse_id", 1),
                connector_id=payload.get("connector_id", 1)
            )

    logger.info("Command %s result for %s: %s", command, charger_id, status)
    return status
