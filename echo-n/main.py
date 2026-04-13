"""
echo-n — OCPP 2.0.1 debug echo server (:5001).

Zero business logic of its own — purely delegates to ``core.V20``
via the server factory.  Identical pattern to ``echo/`` but speaks
OCPP 2.0.1.

Usage:
    python echo-n/main.py

Then connect with:
    wscat -c ws://localhost:5001/ocpp/2.0.1/TEST001 --subprotocol ocpp2.0.1
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import sys

# Ensure the project root is importable when running as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# "echo-n" is not a valid Python identifier, so we use importlib to
# load the V20.server module from the echo-n directory.
_echo_n_v20_server = importlib.import_module("echo-n.V20.server")
create_v201_echo_server = _echo_n_v20_server.create_v201_echo_server

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("echo-n")

ECHO_N_PORT = int(os.getenv("ECHO_N_PORT", "5001"))


async def main():
    server = await create_v201_echo_server("0.0.0.0", ECHO_N_PORT)
    logger.info("Echo-N V201 server ready on :%d", ECHO_N_PORT)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
