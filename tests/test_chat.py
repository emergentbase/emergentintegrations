"""Offline unit tests — no network, no OpenAI API calls."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pytest

from emergentintegrations import ChatError, ImageContent, LlmChat, UserMessage
from emergentintegrations._proxy import (
    DEFAULT_PROXY_URL,
    get_app_identifier,
    get_integration_proxy_url,
    is_emergent_key,
)
from emergentintegrations.llm.chat import LlmChat as LlmChatNested
from emergentintegrations.llm.openai import LlmChat as LlmChatOpenaiShim


class _FakeCompletions:
    def __init__(self, container: Dict[str, Any], response: Any) -> None:
        self._container = container
        self._response = response

    async def create(self, **kwargs: Any) -> Any:
        self._container["call"] = kwargs
        return self._response


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self, container: Dict[str, Any], response: Any) -> None:
        self.chat = _FakeChat(_FakeCompletions(container, response))


def _patch_client(chat: LlmChat, response: Any) -> Dict[str, Any]:
    container: Dict[str, Any] = {}
    chat._client = lambda: _FakeClient(container, response)  # type: ignore[method-assign]
    return container


def _completion(text: str = "hi there") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text, images=None))]
    )


def test_nested_import_paths_resolve_to_same_class() -> None:
    assert LlmChat is LlmChatNested
    assert LlmChat is LlmChatOpenaiShim


def test_is_emergent_key() -> None:
    assert is_emergent_key("sk-emergent-abc123") is True
    assert is_emergent_key("sk-test-1") is False
    assert is_emergent_key("") is False


def test_proxy_url_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTEGRATION_PROXY_URL", raising=False)
    monkeypatch.delenv("integration_proxy_url", raising=False)
    assert get_integration_proxy_url() == DEFAULT_PROXY_URL


def test_proxy_url_env_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTEGRATION_PROXY_URL", "https://upper.example")
    monkeypatch.setenv("integration_proxy_url", "https://lower.example")
    assert get_integration_proxy_url() == "https://upper.example"


def test_app_identifier_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_URL", raising=False)
    monkeypatch.setenv("REACT_APP_BACKEND_URL", "https://app.example")
    assert get_app_identifier() == "https://app.example"


def test_image_mime_inference() -> None:
    assert ImageContent.get_mime_type("iVBORw0KGgo...") == "image/png"
    assert ImageContent.get_mime_type("/9j/4AAQ...") == "image/jpeg"
    assert ImageContent.get_mime_type("R0lGODdh...") == "image/gif"
    assert ImageContent.get_mime_type("UklGRiQ...") == "image/webp"
    assert ImageContent.get_mime_type("unknownprefix") == "image/png"


def test_emergent_key_sets_proxy_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTEGRATION_PROXY_URL", raising=False)
    monkeypatch.delenv("APP_URL", raising=False)
    monkeypatch.delenv("REACT_APP_BACKEND_URL", raising=False)
    chat = LlmChat(api_key="sk-emergent-xyz", session_id="s", system_message="sys")
    assert chat._base_url == f"{DEFAULT_PROXY_URL}/llm"


def test_plain_key_has_no_base_url() -> None:
    chat = LlmChat(api_key="sk-abcdef", session_id="s", system_message="sys")
    assert chat._base_url is None


def test_app_id_header_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_URL", "https://app.example")
    chat = LlmChat(api_key="sk-abcdef", session_id="s", system_message="sys")
    assert chat.custom_headers["X-App-ID"] == "https://app.example"


def test_user_custom_headers_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_URL", "https://app.example")
    chat = LlmChat(
        api_key="sk-abcdef",
        session_id="s",
        system_message="sys",
        custom_headers={"X-Custom": "yes", "X-App-ID": "override"},
    )
    assert chat.custom_headers["X-Custom"] == "yes"
    assert chat.custom_headers["X-App-ID"] == "override"


def test_explicit_base_url_overrides_emergent_routing() -> None:
    chat = LlmChat(
        api_key="sk-emergent-xyz",
        session_id="s",
        system_message="sys",
        base_url="https://custom.example",
    )
    assert chat._base_url == "https://custom.example"


def test_with_model_and_with_params_chain() -> None:
    chat = (
        LlmChat(api_key="sk-a", session_id="s", system_message="sys")
        .with_model("openai", "gpt-4o-mini")
        .with_params(temperature=0.3, max_tokens=128)
    )
    assert chat.model == "gpt-4o-mini"
    assert chat.extra_params == {"temperature": 0.3, "max_tokens": 128}


async def test_send_message_appends_and_returns_text() -> None:
    chat = LlmChat(api_key="sk-a", session_id="s", system_message="sys")
    call = _patch_client(chat, _completion("hello"))

    result = await chat.send_message(UserMessage(text="hi"))

    assert result == "hello"
    assert chat.messages[-1] == {"role": "assistant", "content": "hello"}
    assert call["call"]["model"] == "gpt-4o"
    user_turn = call["call"]["messages"][-2]
    assert user_turn["role"] == "user"
    assert user_turn["content"][0] == {"type": "text", "text": "hi"}


async def test_send_message_includes_image_part() -> None:
    chat = LlmChat(api_key="sk-a", session_id="s", system_message="sys")
    _patch_client(chat, _completion("ok"))

    msg = UserMessage(text="what's this", file_contents=[ImageContent("/9j/4AAQ")])
    await chat.send_message(msg)

    parts = chat.messages[-2]["content"]
    assert parts[0] == {"type": "text", "text": "what's this"}
    assert parts[1]["type"] == "image_url"
    assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,/9j/4AAQ")


async def test_send_message_rejects_empty_user_message() -> None:
    chat = LlmChat(api_key="sk-a", session_id="s", system_message="sys")
    _patch_client(chat, _completion("never reached"))

    with pytest.raises(ChatError):
        await chat.send_message(UserMessage())


async def test_multimodal_response_parses_images() -> None:
    chat = LlmChat(api_key="sk-a", session_id="s", system_message="sys")
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="here it is",
                    images=[
                        {"image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
                    ],
                )
            )
        ]
    )
    _patch_client(chat, response)

    text, images = await chat.send_message_multimodal_response(UserMessage(text="draw"))

    assert text == "here it is"
    assert images == [{"mime_type": "image/png", "data": "ZmFrZQ=="}]
