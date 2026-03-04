"""
Unit tests for backend app security defaults.
"""

from backend.app import resolve_bind_host, is_api_auth_enabled, get_api_auth_token


def test_resolve_bind_host_defaults_to_localhost(monkeypatch):
    """Backend must default to localhost-only binding."""
    monkeypatch.delenv("KORTEX_BIND_HOST", raising=False)
    assert resolve_bind_host() == "127.0.0.1"


def test_resolve_bind_host_reads_env_override(monkeypatch):
    """Binding can be overridden explicitly for trusted local container networks."""
    monkeypatch.setenv("KORTEX_BIND_HOST", "0.0.0.0")
    assert resolve_bind_host() == "0.0.0.0"


def test_api_auth_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KORTEX_REQUIRE_AUTH", raising=False)
    assert is_api_auth_enabled() is False


def test_api_auth_enabled_by_env(monkeypatch):
    monkeypatch.setenv("KORTEX_REQUIRE_AUTH", "true")
    assert is_api_auth_enabled() is True


def test_get_api_auth_token_from_env(monkeypatch):
    monkeypatch.setenv("KORTEX_API_TOKEN", "secret-token")
    assert get_api_auth_token() == "secret-token"
