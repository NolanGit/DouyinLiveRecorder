# -*- encoding: utf-8 -*-
"""URL → live-stream metadata routing.

Receives a recording URL, identifies the platform from the URL, calls the
right handler from :mod:`platform_registry` and returns
``(platform, port_info, new_record_url)``. If the URL is unrecognised raises
:class:`UnknownPlatformError`.
"""
from __future__ import annotations

import uuid

from . import state
from .platform_registry import find_handler


class UnknownPlatformError(ValueError):
    """Raised when no platform handler matches a given URL."""


def _handle_custom_stream(record_url: str) -> tuple[str, dict, str]:
    """Direct ``.flv``/``.m3u8`` URLs are recorded without spider/stream calls."""
    platform = '自定义录制直播'
    port_info: dict = {
        "anchor_name": platform + '_' + str(uuid.uuid4())[:8],
        "is_live": True,
        "record_url": record_url,
    }
    if '.flv' in record_url:
        port_info['flv_url'] = record_url
    else:
        port_info['m3u8_url'] = record_url
    return platform, port_info, ''


def dispatch(record_url: str, record_quality: str,
             monitor_proxy_address: str | None) -> tuple[str, dict, str]:
    """Resolve ``record_url`` → ``(platform, port_info, new_record_url)``."""
    handler = find_handler(record_url)
    if handler is not None:
        return handler(record_url, record_quality, monitor_proxy_address)

    if ".m3u8" in record_url or ".flv" in record_url:
        return _handle_custom_stream(record_url)

    raise UnknownPlatformError(record_url)


__all__ = ["UnknownPlatformError", "dispatch"]
