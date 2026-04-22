"""Compatibility shim matching the import path used by existing Emergent templates.

Historic callers use ``from emergentintegrations.llm.openai import LlmChat``.
The basic SDK exposes the same class via the ``llm.chat`` module; this package
re-exports it so those imports keep working.
"""

from ..chat import (
    ChatError,
    FileContent,
    FileContentWithMimeType,
    ImageContent,
    LlmChat,
    UserMessage,
)

__all__ = [
    "LlmChat",
    "UserMessage",
    "FileContent",
    "FileContentWithMimeType",
    "ImageContent",
    "ChatError",
]
