"""api.decorators — Reusable endpoint decorators."""

from __future__ import annotations

import functools
import logging
from typing import Callable

from flask import jsonify

logger = logging.getLogger(__name__)


def error_handler(func: Callable) -> Callable:
    """Wrap a Flask view so that unhandled exceptions return"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as exc:
            logger.warning("ValueError in %s: %s", func.__name__, exc)
            return jsonify({"error": str(exc)}), 400
        except KeyError as exc:
            logger.warning("KeyError in %s: %s", func.__name__, exc)
            return jsonify({"error": f"Missing key: {exc}"}), 400
        except LookupError as exc:
            logger.warning("LookupError in %s: %s", func.__name__, exc)
            return jsonify({"error": str(exc)}), 404
        except Exception as exc:
            logger.exception("Unhandled error in %s", func.__name__)
            return jsonify({"error": "Internal server error"}), 500

    return wrapper
