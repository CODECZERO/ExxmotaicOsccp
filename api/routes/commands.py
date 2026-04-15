"""
api.routes.commands — Remote charger command endpoints.

Each route delegates to ``command_controller`` for business logic.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from api.decorators import error_handler
from api.controllers import command_controller

commands_bp = Blueprint("commands", __name__, url_prefix="/api")


@commands_bp.route("/chargers/<string:charger_id>/commands", methods=["GET"])
@error_handler
def list_logs(charger_id: str):
    """GET /api/chargers/<id>/commands — command history."""
    data, status = command_controller.list_command_logs(charger_id)
    return jsonify(data), status


@commands_bp.route("/chargers/<string:charger_id>/start", methods=["POST"])
@error_handler
def remote_start(charger_id: str):
    """POST /api/chargers/<id>/start — remote start session."""
    payload = request.get_json(silent=True) or {}
    data, status = command_controller.remote_start(charger_id, payload)
    return jsonify(data), status


@commands_bp.route("/chargers/<string:charger_id>/stop", methods=["POST"])
@error_handler
def remote_stop(charger_id: str):
    """POST /api/chargers/<id>/stop — remote stop session."""
    payload = request.get_json(silent=True) or {}
    data, status = command_controller.remote_stop(charger_id, payload)
    return jsonify(data), status


@commands_bp.route("/chargers/<string:charger_id>/reset", methods=["POST"])
@error_handler
def reset_charger(charger_id: str):
    """POST /api/chargers/<id>/reset — reset charger."""
    payload = request.get_json(silent=True) or {}
    data, status = command_controller.reset(charger_id, payload)
    return jsonify(data), status


@commands_bp.route("/chargers/<string:charger_id>/unlock", methods=["POST"])
@error_handler
def unlock_connector(charger_id: str):
    """POST /api/chargers/<id>/unlock — unlock connector."""
    payload = request.get_json(silent=True) or {}
    data, status = command_controller.unlock(charger_id, payload)
    return jsonify(data), status
