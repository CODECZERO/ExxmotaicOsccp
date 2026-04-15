"""api.routes.chargers — Charger management endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from api.decorators import error_handler
from api.controllers import charger_controller

chargers_bp = Blueprint("chargers", __name__, url_prefix="/api")


@chargers_bp.route("/chargers", methods=["GET"])
@error_handler
def list_chargers():
    """GET /api/chargers — list all chargers."""
    data, status = charger_controller.list_all()
    return jsonify(data), status


@chargers_bp.route("/chargers/<string:charger_id>", methods=["GET"])
@error_handler
def get_charger(charger_id: str):
    """GET /api/chargers/<id> — get single charger + status."""
    data, status = charger_controller.get_by_id(charger_id)
    return jsonify(data), status


@chargers_bp.route("/chargers/<string:charger_id>/sessions", methods=["GET"])
@error_handler
def list_charger_sessions(charger_id: str):
    """GET /api/chargers/<id>/sessions — list all sessions for this charger."""
    from api.controllers import session_controller
    data, status = session_controller.list_by_charger(charger_id)
    return jsonify(data), status


@chargers_bp.route("/chargers", methods=["POST"])
@error_handler
def create_charger():
    """POST /api/chargers — register a new charger."""
    payload = request.get_json(force=True)
    data, status = charger_controller.create(payload)
    return jsonify(data), status


@chargers_bp.route("/chargers/<string:charger_id>", methods=["PUT"])
@error_handler
def update_charger(charger_id: str):
    """PUT /api/chargers/<id> — update charger."""
    payload = request.get_json(force=True)
    data, status = charger_controller.update(charger_id, payload)
    return jsonify(data), status


@chargers_bp.route("/chargers/<string:charger_id>", methods=["DELETE"])
@error_handler
def delete_charger(charger_id: str):
    """DELETE /api/chargers/<id> — remove charger."""
    data, status = charger_controller.delete(charger_id)
    return jsonify(data), status
