"""
echo — OCPP 1.6J debug echo server (:8000).

Zero business logic of its own — purely delegates to ``core.V16``
via the server factory in ``echo.V16.server``.
Use this to smoke-test physical hardware before wiring up
the production core server and database.

Usage:
    python echo/main.py

Then connect with:
    wscat -c ws://localhost:8000/ocpp/1.6/TEST001 --subprotocol ocpp1.6
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Ensure the project root is importable when running as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from echo.V16.server import create_v16_echo_server  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("echo")

ECHO_PORT = int(os.getenv("ECHO_PORT", "8000"))


async def main():
    server = await create_v16_echo_server("0.0.0.0", ECHO_PORT)
    logger.info("Echo V16 server ready on :%d", ECHO_PORT)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
