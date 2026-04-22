# emergent-llm-sdk

Source for the **`emergentintegrations`** Python package — a small async chat client built on top of the [OpenAI SDK](https://github.com/openai/openai-python). Works with any OpenAI-compatible endpoint, and routes through the Emergent integration proxy when given an `sk-emergent-*` key.

> The GitHub repo is `emergent-llm-sdk`; the PyPI distribution and the Python import path are both `emergentintegrations`.

## Install

```bash
pip install emergentintegrations
```

## Quick start

```python
import asyncio
from emergentintegrations import LlmChat, UserMessage, ImageContent
# Existing template code can also keep its original import path:
# from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

async def main():
    chat = (
        LlmChat(
            api_key="sk-...",           # OpenAI key, or sk-emergent-* for proxy routing
            session_id="abc-123",
            system_message="You are a concise assistant.",
        )
        .with_model("openai", "gpt-4o-mini")
        .with_params(temperature=0.3)
    )

    reply = await chat.send_message(UserMessage(text="Give me a haiku about Python."))
    print(reply)

    with_image = UserMessage(
        text="What is in this picture?",
        file_contents=[ImageContent("/9j/4AAQSkZJRg...")],   # JPEG base64
    )
    reply = await chat.send_message(with_image)
    print(reply)

asyncio.run(main())
```

## How routing works

- **Plain key** (`sk-...`, or any OpenAI-compatible provider key) — the SDK talks directly to the OpenAI API (or to whatever endpoint you pass via `base_url=`).
- **Emergent key** (`sk-emergent-*`) — the SDK sets `base_url` to `${INTEGRATION_PROXY_URL:-https://integrations.emergentagent.com}/llm` and lets the Emergent proxy dispatch to the underlying model.
- If `APP_URL` or `REACT_APP_BACKEND_URL` is set, an `X-App-ID` header is added automatically so the proxy can attribute the call.

Environment variables, all optional:

| Name | Purpose |
|---|---|
| `INTEGRATION_PROXY_URL` | Override the default Emergent proxy endpoint. |
| `APP_URL` | App identifier forwarded as `X-App-ID`. |
| `REACT_APP_BACKEND_URL` | Fallback when `APP_URL` is unset. |

## API surface

- `LlmChat(api_key, session_id, system_message, *, initial_messages=None, custom_headers=None, base_url=None)`
- `.with_model(provider, model)` — chainable. Sets the target model string.
- `.with_params(**params)` — chainable. Extra kwargs forwarded to `chat.completions.create`.
- `.send_message(UserMessage) -> str` — async. Returns assistant text.
- `.send_message_multimodal_response(UserMessage) -> (text, images)` — async. `images` is a list of `{"mime_type", "data"}` when the upstream response carries generated images (e.g. via Gemini through the Emergent proxy).
- `UserMessage(text=None, file_contents=None)` — bag of text + file attachments.
- `ImageContent(image_base64)` — infers mime type from the base64 header (PNG/JPEG/GIF/WEBP).
- `FileContentWithMimeType(mime_type, file_path)` — reads a file and packages it with an explicit mime type.

All of the above are importable from either `emergentintegrations`, `emergentintegrations.llm.chat`, or `emergentintegrations.llm.openai` (the latter two paths match the historic layout used by Emergent templates).

## Development

```bash
git clone https://github.com/emergentbase/emergent-llm-sdk
cd emergent-llm-sdk
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0 — see `LICENSE`.
