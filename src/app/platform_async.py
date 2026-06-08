# -*- encoding: utf-8 -*-
"""平台 handler 通用执行助手。

提供 :func:`run_async` 用于在单一 event loop 中合并执行多个协程，
避免每个 handler 内多次 ``asyncio.run`` 重复创建/销毁 event loop 与
连接池的开销。
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Awaitable, Callable

# 每个录制线程复用同一个 event loop。每个 URL 对应一个长生命周期的录制
# 线程，监控期间每隔若干秒轮询一次；旧实现每次轮询都 ``asyncio.run`` 新建
# 并销毁一个 event loop，这里改为按线程缓存 loop，消除反复的 loop 建/销开销。
_thread_local = threading.local()


def _get_loop() -> asyncio.AbstractEventLoop:
    loop = getattr(_thread_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread_local.loop = loop
    return loop


def run_async(coro_factory: Callable[[], Awaitable[Any]]) -> Any:
    """在当前线程复用的 event loop 中执行 ``coro_factory()`` 返回的协程。

    使用方式::

        async def _flow():
            json_data = await spider.get_xxx_stream_data(...)
            return await stream.get_stream_url(json_data, quality)

        port_info = run_async(_flow)

    优势:
    - 每个录制线程仅创建一次 event loop（旧方案每次轮询 ``asyncio.run`` 都新建/销毁）
    - 单次调用内多个协程共享同一 loop，错误堆栈更直接
    """
    # 若当前线程已有正在运行的 loop（极少见，例如嵌套调用），回退到 asyncio.run
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = _get_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro_factory())
    return asyncio.run(coro_factory())
