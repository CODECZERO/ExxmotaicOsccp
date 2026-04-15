"""shared.env — Centralised .env loader."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_loaded = False


def load_env() -> None:
    """
    Load the ``.env`` file from the project root into ``os.environ``.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _loaded
    if _loaded:
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        logger.debug("python-dotenv not installed — skipping .env load")
        _loaded = True
        return

    # Walk up from this file (shared/env.py) to find the project root.
    project_root = Path(__file__).resolve().parent.parent
    dotenv_path = project_root / ".env"

    if dotenv_path.is_file():
        load_dotenv(dotenv_path, override=False)
        logger.info("Loaded environment from %s", dotenv_path)
    else:
        logger.debug(".env file not found at %s — using shell environment", dotenv_path)

    _loaded = True
