"""emergentintegrations — lightweight async LLM chat client on top of the OpenAI SDK."""

from .llm.chat import (
    ChatError,
    FileContent,
    FileContentWithMimeType,
    ImageContent,
    LlmChat,
    UserMessage,
)

__version__ = "0.1.1"

__all__ = [
    "LlmChat",
    "UserMessage",
    "FileContent",
    "FileContentWithMimeType",
    "ImageContent",
    "ChatError",
    "__version__",
]
