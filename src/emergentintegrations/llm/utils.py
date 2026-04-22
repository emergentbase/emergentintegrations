"""Environment helpers kept for backwards compatibility with existing callers."""
from __future__ import annotations

from typing import Optional

from .._proxy import DEFAULT_PROXY_URL
from .._proxy import get_app_identifier as _get_app_identifier
from .._proxy import get_integration_proxy_url as _get_integration_proxy_url


def get_app_identifier() -> Optional[str]:
    return _get_app_identifier()


def get_integration_proxy_url() -> str:
    return _get_integration_proxy_url()


__all__ = ["get_app_identifier", "get_integration_proxy_url", "DEFAULT_PROXY_URL"]
