"""
Deterministic tests for CouncilService.

These tests must not call real network APIs.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from kortex.ai.council import CouncilService


@pytest.mark.asyncio
async def test_council_returns_error_without_openrouter_key(monkeypatch):
    """Council should fail fast when OpenRouter key is missing."""
    monkeypatch.setattr(
        "kortex.ai.council.load_config",
        lambda: {
            "api_keys": {"openrouter": ""},
            "default_provider": "google",
            "default_model": "gemini-3-flash-preview",
            "models": {},
        },
    )

    service = CouncilService()
    result = await asyncio.wait_for(
        service.get_council_response("Hello", [], {"profile": {}}),
        timeout=2.0,
    )

    assert result == {"error": "No OpenRouter API key configured for Council Mode"}


@pytest.mark.asyncio
async def test_council_happy_path_is_deterministic(monkeypatch):
    """Council should aggregate member responses and chairman synthesis deterministically."""
    monkeypatch.setattr(
        "kortex.ai.council.load_config",
        lambda: {
            "api_keys": {"openrouter": "test-key"},
            "default_provider": "google",
            "default_model": "gemini-3-flash-preview",
            "models": {},
        },
    )

    service = CouncilService()
    service._query_gemini = AsyncMock(return_value="gemini answer")
    service._query_gpt52 = AsyncMock(return_value="gpt answer")
    service._query_claude = AsyncMock(return_value="claude answer")
    service._get_peer_reviews = AsyncMock(
        return_value=[{"reviewer": "Member A", "review": "Most actionable: Response B"}]
    )
    service._synthesize_chairman = AsyncMock(return_value="final chairman verdict")

    result = await asyncio.wait_for(
        service.get_council_response("What now?", [{"role": "user", "content": "old"}], {"profile": {}}),
        timeout=2.0,
    )

    assert "council_responses" in result
    assert "peer_reviews" in result
    assert "chairman_response" in result
    assert result["chairman_response"] == "final chairman verdict"
    assert len(result["council_responses"]) == 3
    assert all(item["status"] == "success" for item in result["council_responses"])
    assert result["peer_reviews"][0]["reviewer"] == "Member A"
    service._get_peer_reviews.assert_awaited_once()
    service._synthesize_chairman.assert_awaited_once()


@pytest.mark.asyncio
async def test_council_handles_member_exceptions(monkeypatch):
    """Council should continue when one member task raises an exception."""
    monkeypatch.setattr(
        "kortex.ai.council.load_config",
        lambda: {
            "api_keys": {"openrouter": "test-key"},
            "default_provider": "google",
            "default_model": "gemini-3-flash-preview",
            "models": {},
        },
    )

    service = CouncilService()
    service._query_gemini = AsyncMock(return_value="gemini answer")
    service._query_gpt52 = AsyncMock(side_effect=RuntimeError("gpt failed"))
    service._query_claude = AsyncMock(return_value="claude answer")
    service._get_peer_reviews = AsyncMock(return_value=[])
    service._synthesize_chairman = AsyncMock(return_value="fallback synthesis")

    result = await asyncio.wait_for(
        service.get_council_response("Need advice", [], {"profile": {}}),
        timeout=2.0,
    )

    assert len(result["council_responses"]) == 3
    error_entries = [r for r in result["council_responses"] if r["status"] == "error"]
    assert len(error_entries) == 1
    assert error_entries[0]["model"] == "GPT-5.2"
    assert "gpt failed" in error_entries[0]["response"]
    assert result["chairman_response"] == "fallback synthesis"

