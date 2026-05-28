# -*- encoding: utf-8 -*-
"""Tests for src.app.platform_dispatch — URL dispatch routing."""
import pytest


class TestDispatch:
    """platform_dispatch.dispatch 的核心路由逻辑测试。"""

    def test_custom_flv_stream(self):
        """直接 .flv 链接应被识别为自定义录制。"""
        from src.app.platform_dispatch import dispatch
        platform, port_info, new_url = dispatch(
            "https://example.com/live/stream.flv", "原画", None
        )
        assert platform == "自定义录制直播"
        assert port_info["is_live"] is True
        assert port_info["flv_url"] == "https://example.com/live/stream.flv"
        assert new_url == ""

    def test_custom_m3u8_stream(self):
        """直接 .m3u8 链接应被识别为自定义录制。"""
        from src.app.platform_dispatch import dispatch
        platform, port_info, new_url = dispatch(
            "https://example.com/live/index.m3u8", "原画", None
        )
        assert platform == "自定义录制直播"
        assert port_info["is_live"] is True
        assert port_info["m3u8_url"] == "https://example.com/live/index.m3u8"

    def test_unknown_url_raises(self):
        """无法匹配的 URL 应抛出 UnknownPlatformError。"""
        from src.app.platform_dispatch import UnknownPlatformError, dispatch
        with pytest.raises(UnknownPlatformError):
            dispatch("https://totally-unknown-site.xyz/room/1", "原画", None)

    def test_custom_stream_anchor_name_has_uuid(self):
        """自定义录制的 anchor_name 应包含 UUID 片段。"""
        from src.app.platform_dispatch import dispatch
        _, port_info, _ = dispatch(
            "https://cdn.example.com/hls/live.m3u8", "原画", None
        )
        anchor_name = port_info["anchor_name"]
        assert anchor_name.startswith("自定义录制直播_")
        # UUID 片段长度为 8
        assert len(anchor_name.split("_")[-1]) == 8
