"""Async LLM chat client built on the OpenAI SDK.

Routes to the Emergent integration proxy when the API key begins with
``sk-emergent-``; otherwise talks to OpenAI (or any OpenAI-compatible
endpoint supplied via ``base_url``) directly.
"""
from __future__ import annotations

import base64
import pathlib
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from .._proxy import get_app_identifier, get_integration_proxy_url, is_emergent_key

_IMAGE_MIME_SIGNATURES = (
    ("iVBORw0KGgo", "image/png"),
    ("/9j/", "image/jpeg"),
    ("R0lGOD", "image/gif"),
    ("UklGR", "image/webp"),
)


class ChatError(Exception):
    """Raised for any failure in the chat flow."""


class FileContent:
    def __init__(self, content_type: str, file_content_base64: str) -> None:
        self.content_type = content_type
        self.file_content_base64 = file_content_base64


class ImageContent(FileContent):
    def __init__(self, image_base64: str) -> None:
        super().__init__("image", image_base64)

    @staticmethod
    def get_mime_type(file_content_base64: str) -> str:
        for prefix, mime in _IMAGE_MIME_SIGNATURES:
            if file_content_base64.startswith(prefix):
                return mime
        return "image/png"


class FileContentWithMimeType(FileContent):
    def __init__(self, mime_type: str, file_path: str) -> None:
        data = pathlib.Path(file_path).read_bytes()
        super().__init__(mime_type, base64.b64encode(data).decode("utf-8"))


class UserMessage:
    def __init__(
        self,
        text: Optional[str] = None,
        file_contents: Optional[List[FileContent]] = None,
    ) -> None:
        self.text = text
        self.file_contents = list(file_contents or [])


class LlmChat:
    """Stateful async chat session.

    The conversation history is kept in-memory on the instance. Callers that
    need persistence should serialise ``messages`` themselves.
    """

    def __init__(
        self,
        api_key: str,
        session_id: str,
        system_message: str,
        *,
        initial_messages: Optional[List[Dict[str, Any]]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.session_id = session_id
        self.model = "gpt-4o"
        self.messages: List[Dict[str, Any]] = list(
            initial_messages or [{"role": "system", "content": system_message}]
        )
        self.extra_params: Dict[str, Any] = {}
        self.custom_headers: Dict[str, str] = dict(custom_headers or {})

        app_id = get_app_identifier()
        if app_id:
            self.custom_headers.setdefault("X-App-ID", app_id)

        if base_url is not None:
            self._base_url: Optional[str] = base_url
        elif is_emergent_key(api_key):
            self._base_url = f"{get_integration_proxy_url().rstrip('/')}/llm"
        else:
            self._base_url = None

    def with_model(self, provider: str, model: str) -> "LlmChat":
        """Set the target model.

        ``provider`` is accepted for backwards compatibility. With a direct
        OpenAI key only ``provider="openai"`` works; with an ``sk-emergent-*``
        key the proxy dispatches to the underlying provider and any value is
        accepted.
        """
        del provider  # dispatching happens at the proxy or via base_url
        self.model = model
        return self

    def with_params(self, **params: Any) -> "LlmChat":
        self.extra_params.update(params)
        return self

    async def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def _client(self) -> AsyncOpenAI:
        kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        if self.custom_headers:
            kwargs["default_headers"] = self.custom_headers
        return AsyncOpenAI(**kwargs)

    def _build_user_turn(self, message: UserMessage) -> List[Dict[str, Any]]:
        parts: List[Dict[str, Any]] = []
        if message.text:
            parts.append({"type": "text", "text": message.text})
        for content in message.file_contents:
            if content.content_type == "image":
                mime = ImageContent.get_mime_type(content.file_content_base64)
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{content.file_content_base64}"
                        },
                    }
                )
            else:
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content.content_type};base64,{content.file_content_base64}"
                        },
                    }
                )
        if not parts:
            raise ChatError("UserMessage must contain text or at least one file")
        return [{"role": "user", "content": parts}]

    async def send_message(self, user_message: UserMessage) -> str:
        self.messages.extend(self._build_user_turn(user_message))
        try:
            response = await self._client().chat.completions.create(
                model=self.model,
                messages=self.messages,
                **self.extra_params,
            )
        except Exception as exc:
            raise ChatError(f"Failed to generate chat completion: {exc}") from exc

        try:
            text = response.choices[0].message.content or ""
        except (IndexError, AttributeError) as exc:
            raise ChatError(f"Malformed completion response: {exc}") from exc

        self.messages.append({"role": "assistant", "content": text})
        return text

    async def send_message_multimodal_response(
        self, user_message: UserMessage
    ) -> Tuple[Optional[str], List[Dict[str, str]]]:
        """Send a message and return ``(text, images)``.

        ``images`` is a list of ``{"mime_type", "data"}`` dicts populated when
        the upstream response includes generated images (e.g. when the
        Emergent proxy routes to a Gemini image model). For a plain OpenAI
        chat completion ``images`` is always empty.
        """
        self.messages.extend(self._build_user_turn(user_message))
        try:
            response = await self._client().chat.completions.create(
                model=self.model,
                messages=self.messages,
                **self.extra_params,
            )
        except Exception as exc:
            raise ChatError(f"Failed to generate multimodal completion: {exc}") from exc

        message = response.choices[0].message
        text: Optional[str] = getattr(message, "content", None)
        images: List[Dict[str, str]] = []

        raw_images = getattr(message, "images", None)
        if raw_images:
            for item in raw_images:
                url = (item.get("image_url") or {}).get("url") if isinstance(item, dict) else None
                if not url or ";base64," not in url:
                    continue
                header, _, data = url.partition(";base64,")
                mime = header.removeprefix("data:") or "image/png"
                images.append({"mime_type": mime, "data": data})

        if text:
            self.messages.append({"role": "assistant", "content": text})
        return text, images
