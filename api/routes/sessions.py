"""
api.routes.sessions — Charging session endpoints.

Each route delegates to ``session_controller`` for business logic.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from api.decorators import error_handler
from api.controllers import session_controller

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api")


@sessions_bp.route("/sessions", methods=["GET"])
@error_handler
def list_sessions():
    """GET /api/sessions — list all sessions."""
    data, status = session_controller.list_all()
    return jsonify(data), status


@sessions_bp.route("/sessions/<string:session_id>", methods=["GET"])
@error_handler
def get_session(session_id: str):
    """GET /api/sessions/<id> — session detail + energy consumed."""
    data, status = session_controller.get_by_id(session_id)
    return jsonify(data), status


@sessions_bp.route("/sessions/active", methods=["GET"])
@error_handler
def list_active_sessions():
    """GET /api/sessions/active — all active (un-stopped) sessions."""
    data, status = session_controller.list_active()
    return jsonify(data), status


@sessions_bp.route("/sessions/<string:session_id>/stop", methods=["POST"])
@error_handler
def stop_session(session_id: str):
    """POST /api/sessions/<id>/stop — stop a session."""
    data, status = session_controller.stop(session_id)
    return jsonify(data), status
