"""Emergent proxy helpers — key detection and endpoint resolution."""
from __future__ import annotations

import os
from typing import Optional

EMERGENT_KEY_PREFIX = "sk-emergent-"
DEFAULT_PROXY_URL = "https://integrations.emergentagent.com"


def is_emergent_key(api_key: str) -> bool:
    return api_key.startswith(EMERGENT_KEY_PREFIX)


def get_app_identifier() -> Optional[str]:
    return os.getenv("APP_URL") or os.getenv("REACT_APP_BACKEND_URL")


def get_integration_proxy_url() -> str:
    return (
        os.getenv("INTEGRATION_PROXY_URL")
        or os.getenv("integration_proxy_url")
        or DEFAULT_PROXY_URL
    )
