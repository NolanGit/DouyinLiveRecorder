# -*- encoding: utf-8 -*-
"""Tests for src.app.platform_registry — URL→handler routing logic."""
import pytest


def _get_registry():
    from src.app.platform_registry import HANDLERS, find_handler
    return HANDLERS, find_handler


class TestFindHandler:
    """find_handler 应根据 URL 子串匹配到正确的 handler。"""

    def test_douyin_url_matches(self):
        _, find_handler = _get_registry()
        handler = find_handler("https://live.douyin.com/745964462470")
        assert handler is not None
        assert handler.__name__ == "handle_douyin"

    def test_tiktok_url_matches(self):
        _, find_handler = _get_registry()
        handler = find_handler("https://www.tiktok.com/@user/live")
        assert handler is not None
        assert handler.__name__ == "handle_tiktok"

    def test_bilibili_url_matches(self):
        _, find_handler = _get_registry()
        handler = find_handler("https://live.bilibili.com/21593109")
        assert handler is not None
        assert handler.__name__ == "handle_bilibili"

    def test_twitch_url_matches(self):
        _, find_handler = _get_registry()
        handler = find_handler("https://www.twitch.tv/gamerbee")
        assert handler is not None
        assert handler.__name__ == "handle_twitch"

    def test_youtube_url_matches(self):
        _, find_handler = _get_registry()
        handler = find_handler("https://www.youtube.com/watch?v=abc123")
        assert handler is not None
        assert handler.__name__ == "handle_youtube"

    def test_tuple_key_sooplive_matches(self):
        """tuple 类型的 key（多个子串匹配同一 handler）应正常工作。"""
        _, find_handler = _get_registry()
        h1 = find_handler("https://play.sooplive.co.kr/user1")
        h2 = find_handler("https://play.sooplive.com/user2")
        assert h1 is not None
        assert h1.__name__ == "handle_sooplive"
        assert h2 is not None
        assert h2.__name__ == "handle_sooplive"

    def test_unknown_url_returns_none(self):
        _, find_handler = _get_registry()
        handler = find_handler("https://unknown-platform.example.com/live/123")
        assert handler is None

    def test_empty_url_returns_none(self):
        _, find_handler = _get_registry()
        assert find_handler("") is None

    def test_jd_multiple_keys(self):
        """京东有多个 URL 子串（3.cn, m.jd.com）应都能匹配。"""
        _, find_handler = _get_registry()
        h1 = find_handler("https://3.cn/28MLBy-E")
        h2 = find_handler("https://m.jd.com/live/123")
        assert h1 is not None and h1.__name__ == "handle_jd"
        assert h2 is not None and h2.__name__ == "handle_jd"

    def test_handler_list_is_ordered(self):
        """HANDLERS 列表应该有确定的顺序，确保有 40+ 个条目。"""
        HANDLERS, _ = _get_registry()
        assert len(HANDLERS) >= 40


class TestHandlerListIntegrity:
    """确保注册表中的 handler 都是可调用的。"""

    def test_all_handlers_callable(self):
        HANDLERS, _ = _get_registry()
        for keys, handler in HANDLERS:
            assert callable(handler), f"Handler for {keys} is not callable"

    def test_all_keys_are_str_or_tuple(self):
        HANDLERS, _ = _get_registry()
        for keys, _ in HANDLERS:
            assert isinstance(keys, (str, tuple)), f"Key {keys} is neither str nor tuple"
            if isinstance(keys, tuple):
                for k in keys:
                    assert isinstance(k, str), f"Tuple element {k} is not str"
