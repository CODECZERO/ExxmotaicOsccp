"""
api.routes.meter_values — Meter value query endpoints.

Each route delegates to ``meter_values_controller`` for business logic.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from api.decorators import error_handler
from api.controllers import meter_values_controller

meter_values_bp = Blueprint("meter_values", __name__, url_prefix="/api")


@meter_values_bp.route("/chargers/<string:charger_id>/meter-values", methods=["GET"])
@error_handler
def list_charger_meter_values(charger_id: str):
    """GET /api/chargers/<id>/meter-values — meter readings for a charger."""
    data, status = meter_values_controller.list_by_charger(charger_id)
    return jsonify(data), status


@meter_values_bp.route("/chargers/<string:charger_id>/meter-values/latest", methods=["GET"])
@error_handler
def get_latest_meter_value(charger_id: str):
    """GET /api/chargers/<id>/meter-values/latest — latest reading for a charger."""
    data, status = meter_values_controller.get_latest(charger_id)
    return jsonify(data), status


@meter_values_bp.route("/sessions/<string:session_id>/meter-values", methods=["GET"])
@error_handler
def list_session_meter_values(session_id: str):
    """GET /api/sessions/<id>/meter-values — meter readings for a session."""
    data, status = meter_values_controller.list_by_session(session_id)
    return jsonify(data), status
