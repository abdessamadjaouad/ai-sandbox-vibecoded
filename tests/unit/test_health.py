# tests/unit/test_health.py
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_returns_200():
    """Health check endpoint should return 200 OK."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200


def test_health_endpoint_returns_status():
    """Health check should return status: healthy."""
    with TestClient(app) as client:
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


def test_health_endpoint_returns_app_info():
    """Health check should include app name and version."""
    with TestClient(app) as client:
        response = client.get("/health")
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert data["app"] == "AI Sandbox"
