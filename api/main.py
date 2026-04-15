"""api.main — Flask REST API entry point."""

from __future__ import annotations

import os
import sys

# Ensure the project root is importable when running as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.env import load_env  # noqa: E402

load_env()

from shared.constants import API_PORT, BIND_HOST  # noqa: E402
from api import create_app                         # noqa: E402

if __name__ == "__main__":
    app = create_app()
    app.run(host=BIND_HOST, port=API_PORT, debug=True)
