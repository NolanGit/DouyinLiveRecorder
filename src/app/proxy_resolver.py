# -*- encoding: utf-8 -*-
"""Per-stage proxy address resolver.

Decides which proxy (if any) to use for either monitoring or recording for a
given URL. Pure function with one global state read for the proxy lists.
"""
from __future__ import annotations

from . import state


def get_stage_proxy_address(record_url: str, enable_proxy: bool) -> str | None:
    """Return the proxy URL for the given live URL or ``None``.

    The decision considers:

    * ``enable_proxy`` flag (per stage: monitoring / recording)
    * Global ``use_proxy`` switch
    * Domain-based allow lists ``enable_proxy_platform_list`` and
      ``extra_enable_proxy_platform_list``
    """
    if not enable_proxy or not state.use_proxy:
        return None
    if not state.proxy_addr_bak:
        return None

    for platform_name in state.enable_proxy_platform_list or []:
        platform_name = platform_name.strip()
        if platform_name and platform_name in record_url:
            return state.proxy_addr_bak

    for platform_name in state.extra_enable_proxy_platform_list or []:
        platform_name = platform_name.strip()
        if platform_name and platform_name in record_url:
            return state.proxy_addr_bak

    return None
