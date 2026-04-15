"""api — Flask REST API package."""

from __future__ import annotations

import os
from flask import Flask
from flask_cors import CORS

from api.routes import register_routes
from shared.constants import SECRET_KEY


def create_app() -> Flask:
    """Application factory — builds the Flask app with all blueprints registered."""
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.config["SECRET_KEY"] = SECRET_KEY
    app.config.setdefault("JSON_SORT_KEYS", False)

    register_routes(app)


    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def internal_error(e):
        return {"error": "Internal server error"}, 500

    return app
