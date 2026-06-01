# -*- encoding: utf-8 -*-
"""平台 handler 通用执行助手。

提供 :func:`run_async` 用于在单一 event loop 中合并执行多个协程，
避免每个 handler 内多次 ``asyncio.run`` 重复创建/销毁 event loop 与
连接池的开销。
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable


def run_async(coro_factory: Callable[[], Awaitable[Any]]) -> Any:
    """在单一 event loop 中执行 ``coro_factory()`` 返回的协程。

    使用方式::

        async def _flow():
            json_data = await spider.get_xxx_stream_data(...)
            return await stream.get_stream_url(json_data, quality)

        port_info = run_async(_flow)

    优势:
    - 单次 event loop 创建/销毁（原方案两次 ``asyncio.run`` 至少两次）
    - 协程内的 ``httpx.AsyncClient`` 可复用（减少 SSL 握手开销）
    - 错误堆栈更直接（无需穿过两个 loop）
    """
    return asyncio.run(coro_factory())
