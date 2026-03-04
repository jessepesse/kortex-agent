"""Route-level response schema tests for standardized envelopes."""

from unittest.mock import AsyncMock

import pytest
import asyncio

from backend.app import create_app
from kortex import data


@pytest.fixture
def app(temp_data_dir, temp_config_file):
    application = create_app()
    application.config["TESTING"] = True
    return application


def _assert_success_envelope(payload):
    assert payload["success"] is True
    assert "data" in payload


def _assert_error_envelope(payload):
    assert payload["error"] is True
    assert isinstance(payload["message"], str)
    assert payload["message"]


def _normalize_result(result):
    if isinstance(result, tuple):
        response, status = result
        return response.get_json(), status
    return result.get_json(), result.status_code


async def _call_async_view(app, endpoint, path, req_json):
    view = app.view_functions[endpoint]
    with app.test_request_context(path, method="POST", json=req_json):
        result = await view()
    return _normalize_result(result)


class TestChatRouteSchemas:
    @pytest.mark.asyncio
    async def test_chat_validation_error_envelope(self, app):
        payload, status = await _call_async_view(app, "chat", "/api/chat", {"message": "", "files": []})
        assert status == 400
        _assert_error_envelope(payload)

    @pytest.mark.asyncio
    async def test_chat_success_envelope(self, app, monkeypatch):
        class _FakeLoop:
            def run_in_executor(self, _executor, fn, *args):
                future = asyncio.Future()
                future.set_result(fn(*args))
                return future

        monkeypatch.setattr(
            "backend.routes.chat.config.load_config",
            lambda: {
                "api_keys": {"google": "test-key", "openrouter": ""},
                "default_provider": "google",
                "default_model": "gemini-3-flash-preview",
                "models": {},
            },
        )
        monkeypatch.setattr("backend.routes.chat.ai_handler.get_ai_response", lambda *args, **kwargs: {"response": "ok"})
        monkeypatch.setattr("backend.routes.chat.asyncio.get_event_loop", lambda: _FakeLoop())
        monkeypatch.setattr("kortex.ai.scribe.ScribeService.analyze_and_update", AsyncMock(return_value=[]))
        monkeypatch.setattr(
            "kortex.ai.scout.scout_analyze",
            AsyncMock(return_value={"decision": "NO_SEARCH", "confidence": 75}),
        )

        payload, status = await _call_async_view(
            app,
            "chat",
            "/api/chat",
            {"message": "Hello", "history": [{"role": "user", "content": "prev"}]},
        )
        assert status == 200
        _assert_success_envelope(payload)
        assert payload["data"]["response"] == "ok"
        assert "chat_id" in payload["data"]

    @pytest.mark.asyncio
    async def test_chat_websearch_success_envelope(self, app, monkeypatch):
        monkeypatch.setattr(
            "backend.routes.chat.config.load_config",
            lambda: {
                "api_keys": {"openrouter": ""},
                "default_provider": "google",
                "default_model": "gemini-3-flash-preview",
                "models": {},
            },
        )
        monkeypatch.setattr(
            "kortex.ai.websearch.web_search_response",
            AsyncMock(
                return_value={
                    "response": "search result",
                    "search_type": "NEWS",
                    "specialist_model": "grok-4.1-fast",
                    "sources": [{"url": "https://example.com"}],
                    "scout": {"decision": "FORCE_SEARCH", "confidence": 100},
                }
            ),
        )

        payload, status = await _call_async_view(
            app,
            "chat_websearch",
            "/api/chat/websearch",
            {"message": "latest news", "history": [{"role": "user", "content": "prev"}]},
        )
        assert status == 200
        _assert_success_envelope(payload)
        assert payload["data"]["response"] == "search result"

    @pytest.mark.asyncio
    async def test_chat_scout_success_envelope(self, app, monkeypatch):
        monkeypatch.setattr(
            "kortex.ai.scout.scout_analyze",
            AsyncMock(
                return_value={
                    "decision": "SUGGEST_SEARCH",
                    "confidence": 88,
                    "search_type": "RESEARCH",
                    "reason": "Needs fresh external data",
                    "recommended_model": "perplexity",
                }
            ),
        )
        payload, status = await _call_async_view(
            app,
            "chat_scout",
            "/api/chat/scout",
            {"message": "analyze this", "history": []},
        )
        assert status == 200
        _assert_success_envelope(payload)
        assert payload["data"]["decision"] == "SUGGEST_SEARCH"


class TestCouncilRouteSchemas:
    @pytest.mark.asyncio
    async def test_council_success_envelope(self, app, temp_data_dir, monkeypatch):
        chat_id = data.generate_chat_id()
        data.save_conversation(chat_id, [], "Existing")
        monkeypatch.setattr(
            "kortex.ai.council.CouncilService.get_council_response",
            AsyncMock(
                return_value={
                    "council_responses": [],
                    "peer_reviews": [],
                    "chairman_response": "Council verdict",
                }
            ),
        )

        payload, status = await _call_async_view(
            app,
            "council",
            "/api/council",
            {"chat_id": chat_id, "message": "Question", "history": [{"role": "user", "content": "prev"}]},
        )
        assert status == 200
        _assert_success_envelope(payload)
        assert payload["data"]["chairman_response"] == "Council verdict"

    @pytest.mark.asyncio
    async def test_council_validation_error_envelope(self, app):
        payload, status = await _call_async_view(app, "council", "/api/council", {"message": ""})
        assert status == 400
        _assert_error_envelope(payload)
