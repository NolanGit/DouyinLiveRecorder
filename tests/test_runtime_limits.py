# -*- encoding: utf-8 -*-
"""并发闸门、错误计数和 HTTP 客户端复用。"""
import asyncio
import threading

from src.app import state
from src.app.recorder import _record_error
from src.http_clients.async_http import _get_client


def test_record_error_only_increments_count():
    state.error_count = 0
    state.error_window = []
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        _record_error(exc)
    assert state.error_count == 1
    assert state.error_window == []


def test_limiter_blocks_until_release():
    limiter = state.ConcurrencyLimiter(1)
    entered = threading.Event()
    release = threading.Event()
    second = threading.Event()

    def hold():
        with limiter:
            entered.set()
            release.wait(2)

    def acquire():
        with limiter:
            second.set()

    first = threading.Thread(target=hold)
    other = threading.Thread(target=acquire)
    first.start()
    assert entered.wait(2)
    other.start()
    other.join(0.1)
    assert not second.is_set()
    release.set()
    other.join(2)
    first.join(2)
    assert second.is_set()


def test_limiter_set_limit_unblocks_waiters():
    limiter = state.ConcurrencyLimiter(1)
    started = threading.Event()
    done = threading.Event()

    def hold():
        with limiter:
            started.set()
            done.wait(2)

    def acquire():
        with limiter:
            done.set()

    threading.Thread(target=hold).start()
    assert started.wait(2)
    waiter = threading.Thread(target=acquire)
    waiter.start()
    waiter.join(0.1)
    assert not done.is_set()
    limiter.set_limit(2)
    waiter.join(2)
    assert done.is_set()


def test_http_client_reused_on_same_loop():
    async def _go():
        first = await _get_client(None, False, False)
        second = await _get_client(None, False, False)
        assert first is second
        await first.aclose()

    asyncio.run(_go())
