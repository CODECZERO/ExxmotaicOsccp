"""
api.routes.stats — Dashboard statistics endpoints.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from api.decorators import error_handler
from api.controllers import stats_controller

stats_bp = Blueprint("stats", __name__, url_prefix="/api")


@stats_bp.route("/stats", methods=["GET"])
@error_handler
def dashboard_stats():
    """GET /api/stats — platform-wide dashboard statistics."""
    data, status = stats_controller.get_dashboard()
    return jsonify(data), status


@stats_bp.route("/chargers/<string:charger_id>/stats", methods=["GET"])
@error_handler
def charger_stats(charger_id: str):
    """GET /api/chargers/<id>/stats — statistics for a specific charger."""
    data, status = stats_controller.get_charger_stats(charger_id)
    return jsonify(data), status
