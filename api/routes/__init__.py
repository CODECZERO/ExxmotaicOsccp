"""api.routes — Blueprint registration."""

from __future__ import annotations

from flask import Flask

from api.routes.health import health_bp
from api.routes.chargers import chargers_bp
from api.routes.sessions import sessions_bp
from api.routes.commands import commands_bp
from api.routes.meter_values import meter_values_bp
from api.routes.stats import stats_bp


def register_routes(app: Flask) -> None:
    """Register all API blueprints on *app*."""
    app.register_blueprint(health_bp)
    app.register_blueprint(chargers_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(commands_bp)
    app.register_blueprint(meter_values_bp)
    app.register_blueprint(stats_bp)
