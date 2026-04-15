"""tests.test_api — Integration tests for the Flask REST API."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from api import create_app
from shared.db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up an in-memory database for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing."""
    Base.metadata.create_all(bind=engine)
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app) -> FlaskClient:
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def override_get_db(monkeypatch):
    """Override the get_db dependency in the controllers to use our test DB."""
    import shared.db.client

    def mock_get_db():
        class MockContextManager:
            def __enter__(self):
                self.db = TestingSessionLocal()
                return self.db
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.db.rollback()
                else:
                    self.db.commit()
                self.db.close()
        return MockContextManager()
    
    monkeypatch.setattr("shared.db.client.db_available", lambda: True)
    monkeypatch.setattr("api.controllers.charger_controller.get_db", mock_get_db)
    monkeypatch.setattr("api.controllers.session_controller.get_db", mock_get_db)
    monkeypatch.setattr("api.controllers.command_controller.get_db", mock_get_db)
    monkeypatch.setattr("api.controllers.meter_values_controller.get_db", mock_get_db)
    monkeypatch.setattr("api.controllers.stats_controller.get_db", mock_get_db)
    
    monkeypatch.setattr("api.controllers.charger_controller.db_available", lambda: True)
    monkeypatch.setattr("api.controllers.session_controller.db_available", lambda: True)
    monkeypatch.setattr("api.controllers.command_controller.db_available", lambda: True)
    monkeypatch.setattr("api.controllers.meter_values_controller.db_available", lambda: True)
    monkeypatch.setattr("api.controllers.stats_controller.db_available", lambda: True)


def test_health_check(client: FlaskClient):
    """Test the HAProxy health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_charger_crud(client: FlaskClient):
    """Test creating, reading, and listing chargers."""
    # 1. Create a charger
    payload = {
        "charger_id": "TEST_CHG_001",
        "vendor": "TKT",
        "model": "DC-60kW"
    }
    response = client.post("/api/chargers", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["charger"]["charger_id"] == "TEST_CHG_001"
    
    # 2. Get the charger
    response = client.get("/api/chargers/TEST_CHG_001")
    assert response.status_code == 200
    assert response.get_json()["charger"]["charger_id"] == "TEST_CHG_001"
    
    # 3. List all chargers
    response = client.get("/api/chargers")
    assert response.status_code == 200
    assert response.get_json()["count"] >= 1
    
    # 4. Check stats endpoint
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.get_json()["stats"]["chargers"]["total"] >= 1


def test_remote_commands(client: FlaskClient):
    """Test the remote command endpoints to verify CommandLog inserts."""
    payload = {
        "charger_id": "TEST_CHG_002",
        "vendor": "TKT",
        "model": "AC-22kW"
    }
    client.post("/api/chargers", json=payload)
    
    # Send a remote start command
    response = client.post("/api/chargers/TEST_CHG_002/start", json={"id_tag": "USER123"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "Accepted"
    
    # Verify command history
    response = client.get("/api/chargers/TEST_CHG_002/commands")
    assert response.status_code == 200
    logs = response.get_json()["command_logs"]
    assert len(logs) == 1
    assert logs[0]["command"] == "RemoteStartTransaction"
