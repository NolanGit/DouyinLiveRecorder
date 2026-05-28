# -*- encoding: utf-8 -*-
"""Tests for src.spider — re-export compatibility entry."""


class TestSpiderReExport:
    """确保 src.spider 作为兼容入口正确 re-export 所有函数。"""

    def test_common_utilities_accessible(self):
        from src import spider
        assert hasattr(spider, "ssl_context")
        assert hasattr(spider, "OptionalStr")
        assert hasattr(spider, "OptionalDict")
        assert hasattr(spider, "get_params")
        assert hasattr(spider, "get_play_url_list")

    def test_douyin_functions_accessible(self):
        from src import spider
        assert callable(spider.get_douyin_stream_data)
        assert callable(spider.get_douyin_web_stream_data)
        assert callable(spider.get_douyin_app_stream_data)

    def test_bilibili_functions_accessible(self):
        from src import spider
        assert callable(spider.get_bilibili_stream_data)
        assert callable(spider.get_bilibili_room_info)
        assert callable(spider.get_bilibili_room_info_h5)

    def test_overseas_platforms_accessible(self):
        from src import spider
        assert callable(spider.get_tiktok_stream_data)
        assert callable(spider.get_twitchtv_stream_data)
        assert callable(spider.get_youtube_stream_url)
        assert callable(spider.get_sooplive_stream_data)

    def test_all_list_matches_exports(self):
        """__all__ 中列出的每个名称都应在模块中存在。"""
        from src import spider
        for name in spider.__all__:
            assert hasattr(spider, name), f"{name} in __all__ but not found in module"

    def test_stream_py_style_import(self):
        """验证 stream.py 的 import 方式仍然有效。"""
        from src.spider import get_douyu_stream_data, get_bilibili_stream_data
        assert callable(get_douyu_stream_data)
        assert callable(get_bilibili_stream_data)

    def test_total_exported_count(self):
        """确保 re-export 的函数数量完整（>=70）。"""
        from src import spider
        assert len(spider.__all__) >= 70
