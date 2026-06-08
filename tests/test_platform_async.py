# -*- encoding: utf-8 -*-
"""Tests for :mod:`src.app.platform_async.run_async`."""
import asyncio
import threading

from src.app.platform_async import run_async


def test_run_async_returns_result():
    async def _flow():
        await asyncio.sleep(0)
        return 42

    assert run_async(_flow) == 42


def test_run_async_reuses_loop_within_thread():
    loops = []

    async def _flow():
        loops.append(asyncio.get_event_loop())
        return True

    run_async(_flow)
    run_async(_flow)
    assert loops[0] is loops[1]


def test_run_async_isolated_per_thread():
    seen = {}

    async def _flow(key):
        seen[key] = id(asyncio.get_event_loop())
        return True

    def worker(key):
        run_async(lambda: _flow(key))

    t1 = threading.Thread(target=worker, args=("a",))
    t2 = threading.Thread(target=worker, args=("b",))
    t1.start(); t1.join()
    t2.start(); t2.join()
    assert seen["a"] != seen["b"]
