"""
Integration tests for optional API auth guard.
"""

import pytest


@pytest.fixture
def auth_client(temp_data_dir, temp_config_file, monkeypatch):
    """Create client with API auth enabled and token configured."""
    from backend.app import create_app

    monkeypatch.setenv("KORTEX_REQUIRE_AUTH", "true")
    monkeypatch.setenv("KORTEX_API_TOKEN", "test-token")

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client_missing_token(temp_data_dir, temp_config_file, monkeypatch):
    """Create client with auth enabled but missing token configuration."""
    from backend.app import create_app

    monkeypatch.setenv("KORTEX_REQUIRE_AUTH", "true")
    monkeypatch.delenv("KORTEX_API_TOKEN", raising=False)

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


class TestApiAuthGuard:
    def test_health_endpoint_is_public(self, auth_client):
        response = auth_client.get("/api/health")
        assert response.status_code == 200

    def test_api_requires_bearer_token_when_enabled(self, auth_client):
        response = auth_client.get("/api/config")
        assert response.status_code == 401
        payload = response.get_json()
        assert payload["error"] is True
        assert payload["message"] == "Unauthorized"

    def test_api_rejects_invalid_token(self, auth_client):
        response = auth_client.get(
            "/api/config",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_api_accepts_valid_token(self, auth_client):
        response = auth_client.get(
            "/api/config",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "providers" in payload["data"]

    def test_missing_token_config_returns_503(self, auth_client_missing_token):
        response = auth_client_missing_token.get("/api/config")
        assert response.status_code == 503
        payload = response.get_json()
        assert payload["error"] is True
        assert "KORTEX_API_TOKEN" in payload["message"]
