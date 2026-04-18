"""core.dispatcher — Connection registry and command polling logic."""

import asyncio
import logging
from typing import Dict, Any

from shared.db.client import get_db, db_available
from shared.db.models import CommandLog
from core.V16.charge_point import V16ChargePoint
from core.V20.charge_point import V201ChargePoint

logger = logging.getLogger(__name__)

# Registry of active chargers connected to THIS process
# Key: charger_id (str), Value: ChargePoint instance
active_connections: Dict[str, Any] = {}

async def start_command_poller(interval: float = 2.0):
    """
    Background loop that polls the DB for 'Pending' commands for ANY charger
    currently connected to this specific process.
    """
    logger.info("Starting CommandPoller loop (interval=%.1fs)", interval)
    
    while True:
        if not db_available():
            await asyncio.sleep(interval)
            continue
            
        try:
            # We only look for commands where status is 'Accepted' (meaning the API received it)
            # but hasn't been 'Processed' by the WebSocket server yet.
            # In our command_controller, we set status="Accepted" by default.
            
            with get_db() as db:
                if db is None:
                    await asyncio.sleep(interval)
                    continue
                
                # Find pending commands for chargers we are actually hosting
                pending = (
                    db.query(CommandLog)
                    .filter(CommandLog.status == "Accepted")
                    .filter(CommandLog.charger_id.in_(active_connections.keys()))
                    .all()
                )
                
                for cmd in pending:
                    await _dispatch_command(cmd)
                    db.commit() # Update status to 'Processed' or 'Failed'
                    
        except Exception:
            logger.exception("Error in CommandPoller loop")
            
        await asyncio.sleep(interval)

async def _dispatch_command(cmd: CommandLog):
    """Attempt to send the command to the physical charger via its active socket."""
    charger_id = cmd.charger_id
    cp = active_connections.get(charger_id)
    
    if not cp:
        # Should not happen because of the SQL filter, but safe-guard
        return

    logger.info("Dispatching command %s to charger %s", cmd.command, charger_id)
    
    try:
        status = "Failed"
        payload = cmd.payload or {}
        
        if isinstance(cp, V16ChargePoint):
            if cmd.command == "RemoteStartTransaction":
                status = await cp.remote_start(
                    id_tag=payload.get("id_tag", "UNKNOWN"),
                    connector_id=payload.get("connector_id", 1)
                )
            elif cmd.command == "RemoteStopTransaction":
                status = await cp.remote_stop(
                    transaction_id=int(payload.get("transaction_id", 0))
                )
            elif cmd.command == "Reset":
                status = await cp.reset(reset_type=payload.get("type", "Soft"))
            elif cmd.command == "UnlockConnector":
                status = await cp.unlock(connector_id=payload.get("connector_id", 1))
                
        elif isinstance(cp, V201ChargePoint):
            # OCPP 2.0.1 equivalents
            if cmd.command == "RemoteStartTransaction":
                status = await cp.request_start(
                    id_tag=payload.get("id_tag", "UNKNOWN"),
                    evse_id=payload.get("evse_id", 1)
                )
            elif cmd.command == "RemoteStopTransaction":
                status = await cp.request_stop(
                    transaction_id=str(payload.get("transaction_id", ""))
                )
            elif cmd.command == "Reset":
                status = await cp.reset(reset_type=payload.get("type", "OnIdle"))
            elif cmd.command == "UnlockConnector":
                status = await cp.unlock(
                    evse_id=payload.get("evse_id", 1),
                    connector_id=payload.get("connector_id", 1)
                )

        cmd.status = status # e.g. 'Accepted', 'Rejected', 'Unlocked'
        logger.info("Command %s result for %s: %s", cmd.command, charger_id, status)
        
    except Exception as e:
        logger.exception("Failed to dispatch command to %s", charger_id)
        cmd.status = f"Error: {str(e)[:28]}"
