# -*- encoding: utf-8 -*-
"""Tests for src.spiders.base — common spider utility functions."""
import pytest


class TestGetParams:
    """get_params 从 URL query string 中提取指定参数。"""

    def test_extract_existing_param(self):
        from src.spiders.base import get_params
        url = "https://example.com/live?room_id=12345&quality=HD"
        assert get_params(url, "room_id") == "12345"
        assert get_params(url, "quality") == "HD"

    def test_missing_param_returns_none(self):
        from src.spiders.base import get_params
        url = "https://example.com/live?room_id=12345"
        assert get_params(url, "nonexist") is None

    def test_empty_url(self):
        from src.spiders.base import get_params
        assert get_params("", "key") is None

    def test_url_without_query_string(self):
        from src.spiders.base import get_params
        url = "https://example.com/live/room123"
        assert get_params(url, "room") is None

    def test_param_with_special_characters(self):
        from src.spiders.base import get_params
        url = "https://example.com/?name=%E6%B5%8B%E8%AF%95&id=1"
        assert get_params(url, "name") == "测试"
        assert get_params(url, "id") == "1"

    def test_multiple_values_returns_first(self):
        """多个同名参数时返回第一个值。"""
        from src.spiders.base import get_params
        url = "https://example.com/?tag=a&tag=b&tag=c"
        assert get_params(url, "tag") == "a"


class TestGetPlayUrlList:
    """get_play_url_list 解析 m3u8 播放列表并按带宽排序。"""

    def test_parse_m3u8_with_bandwidth(self, monkeypatch):
        """带 BANDWIDTH 标记的 m3u8 应按带宽降序排列。"""
        import asyncio
        from src.spiders import base

        m3u8_content = (
            "#EXTM3U\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=500000\n"
            "https://cdn.example.com/low.m3u8\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=2000000\n"
            "https://cdn.example.com/high.m3u8\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=1000000\n"
            "https://cdn.example.com/mid.m3u8\n"
        )

        async def mock_async_req(**kwargs):
            return m3u8_content

        monkeypatch.setattr(base, "async_req", mock_async_req)
        result = asyncio.run(base.get_play_url_list("https://example.com/master.m3u8"))
        assert result == [
            "https://cdn.example.com/high.m3u8",
            "https://cdn.example.com/mid.m3u8",
            "https://cdn.example.com/low.m3u8",
        ]

    def test_parse_m3u8_relative_paths(self, monkeypatch):
        """无 https:// 前缀但以 m3u8 结尾的行应被提取。"""
        import asyncio
        from src.spiders import base

        m3u8_content = (
            "#EXTM3U\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=3000000\n"
            "stream_high.m3u8\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=1000000\n"
            "stream_low.m3u8\n"
        )

        async def mock_async_req(**kwargs):
            return m3u8_content

        monkeypatch.setattr(base, "async_req", mock_async_req)
        result = asyncio.run(base.get_play_url_list("https://example.com/master.m3u8"))
        assert result == ["stream_high.m3u8", "stream_low.m3u8"]


class TestSslContext:
    """ssl_context 应禁用证书验证。"""

    def test_ssl_context_no_verify(self):
        import ssl
        from src.spiders.base import ssl_context
        assert ssl_context.check_hostname is False
        assert ssl_context.verify_mode == ssl.CERT_NONE


class TestTypeAliases:
    """类型别名应正确定义。"""

    def test_optional_str(self):
        from src.spiders.base import OptionalStr
        # str | None 等价于 Optional[str]
        assert OptionalStr == (str | None)

    def test_optional_dict(self):
        from src.spiders.base import OptionalDict
        assert OptionalDict == (dict | None)
