"""Emergent proxy helpers — key detection and endpoint resolution."""

from __future__ import annotations

import os

EMERGENT_KEY_PREFIX = "sk-emergent-"
DEFAULT_PROXY_URL = "https://integrations.emergentagent.com"


def is_emergent_key(api_key: str) -> bool:
    return api_key.startswith(EMERGENT_KEY_PREFIX)


def get_app_identifier() -> str | None:
    return os.getenv("APP_URL") or os.getenv("REACT_APP_BACKEND_URL")


def get_integration_proxy_url() -> str:
    # The lowercase fallback is intentional — matches the legacy CDN-published SDK.
    return (
        os.getenv("INTEGRATION_PROXY_URL")
        or os.getenv("integration_proxy_url")  # noqa: SIM112
        or DEFAULT_PROXY_URL
    )
