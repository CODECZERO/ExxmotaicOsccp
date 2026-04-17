"""
api.routes.health — Health check endpoint.

HAProxy and monitoring tools hit this to know the API is alive.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return a simple JSON health indicator."""
    return jsonify({"status": "ok"}), 200
