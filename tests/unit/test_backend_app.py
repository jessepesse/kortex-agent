"""
Unit tests for backend app security defaults.
"""

from backend.app import resolve_bind_host


def test_resolve_bind_host_defaults_to_localhost(monkeypatch):
    """Backend must default to localhost-only binding."""
    monkeypatch.delenv("KORTEX_BIND_HOST", raising=False)
    assert resolve_bind_host() == "127.0.0.1"


def test_resolve_bind_host_reads_env_override(monkeypatch):
    """Binding can be overridden explicitly for trusted local container networks."""
    monkeypatch.setenv("KORTEX_BIND_HOST", "0.0.0.0")
    assert resolve_bind_host() == "0.0.0.0"

