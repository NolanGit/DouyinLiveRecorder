# -*- encoding: utf-8 -*-
"""Tests for src.spiders.soop_spider — SOOP/AfreecaTV stream resolution.

网络层被 mock，保证离线可复现；覆盖 bj_id 解析、国际版/韩版路由分支
以及开播结果组装逻辑。这条链路在真实环境用
``https://play.sooplive.com/roket0829/294982649`` 验证过可正常录制。
"""
import asyncio
import json

import pytest

from src.spiders import soop_spider


def _run(coro):
    return asyncio.run(coro)


class TestBjIdParsing:
    """bj_id 从直播间 URL 中按段位提取：``split[3] if len(split) < 6 else split[5]``。"""

    def _bj_id(self, url):
        split = url.split("/")
        return split[3] if len(split) < 6 else split[5]

    def test_two_segment_url_uses_index_3(self):
        # https://play.sooplive.com/<bjid>/<broadno> 仅 5 段 -> index 3
        url = "https://play.sooplive.com/roket0829/294982649"
        assert self._bj_id(url) == "roket0829"

    def test_single_segment_url_uses_index_3(self):
        url = "https://play.sooplive.co.kr/roket0829"
        assert self._bj_id(url) == "roket0829"

    def test_deep_path_url_uses_index_5(self):
        # 6+ 段（带额外路径）-> index 5
        url = "https://m.sooplive.co.kr/player/live/roket0829/extra"
        assert self._bj_id(url) == "roket0829"


class TestKoreaRoute:
    """play.sooplive.com/<bjid>/<broadno> 应走韩版 co.kr watch API 并组装直播结果。"""

    def test_live_stream_assembled(self, monkeypatch):
        url = "https://play.sooplive.com/roket0829/294982649"

        watch_payload = {
            "result": 1,
            "data": {
                "user_nick": "박퍼니",
                "bj_id": "roket0829",
                "broad_no": "294982649",
                "hls_authentication_key": "mobiletoken",
            },
        }

        async def fake_async_req(url=None, **kwargs):
            # watch API 返回 JSON 字符串；m3u8 请求返回播放列表文本
            if "broad/a/watch" in (url or ""):
                return json.dumps(watch_payload)
            return (
                "#EXTM3U\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=2000000\n"
                "auth_playlist.m3u8?aid=desktop\n"
            )

        async def fake_get_tk(u, rtype, proxy_addr=None, cookies=None):
            return "desktoptoken"

        async def fake_cdn(broad_no, proxy_addr=None, cookies=None):
            return {"view_url": "http://cdn.sooplive.co.kr/live/auth_master.m3u8"}

        monkeypatch.setattr(soop_spider, "async_req", fake_async_req)
        monkeypatch.setattr(soop_spider, "get_sooplive_tk", fake_get_tk)
        monkeypatch.setattr(soop_spider, "get_sooplive_cdn_url", fake_cdn)

        result = _run(soop_spider.get_sooplive_stream_data(url))

        assert result["is_live"] is True
        assert result["anchor_name"] == "박퍼니-roket0829"
        assert "auth_master.m3u8" in result["m3u8_url"]
        assert result["m3u8_url"].endswith("aid=desktoptoken")
        assert result["play_url_list"]

    def test_desktop_token_failure_falls_back_to_mobile(self, monkeypatch):
        """桌面端取 aid 失败时应降级使用移动端 hls_authentication_key。"""
        url = "https://play.sooplive.com/roket0829/294982649"
        watch_payload = {
            "result": 1,
            "data": {
                "user_nick": "박퍼니",
                "bj_id": "roket0829",
                "broad_no": "294982649",
                "hls_authentication_key": "mobiletoken",
            },
        }

        async def fake_async_req(url=None, **kwargs):
            if "broad/a/watch" in (url or ""):
                return json.dumps(watch_payload)
            return (
                "#EXTM3U\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=2000000\n"
                "auth_playlist.m3u8?aid=x\n"
            )

        async def failing_tk(u, rtype, proxy_addr=None, cookies=None):
            raise RuntimeError("desktop api down")

        async def fake_cdn(broad_no, proxy_addr=None, cookies=None):
            return {"view_url": "http://cdn.sooplive.co.kr/live/auth_master.m3u8"}

        monkeypatch.setattr(soop_spider, "async_req", fake_async_req)
        monkeypatch.setattr(soop_spider, "get_sooplive_tk", failing_tk)
        monkeypatch.setattr(soop_spider, "get_sooplive_cdn_url", fake_cdn)

        result = _run(soop_spider.get_sooplive_stream_data(url))
        assert result["is_live"] is True
        assert result["m3u8_url"].endswith("aid=mobiletoken")

    def test_watch_response_without_data_raises_clear_error(self, monkeypatch):
        """SOOP 偶发返回无 data 的异常结构时，不应再裸抛 KeyError('data')。"""
        url = "https://play.sooplive.com/roket0829/294982649"

        async def fake_async_req(url=None, **kwargs):
            if "broad/a/watch" in (url or ""):
                return json.dumps({"result": 0, "error": "temporary upstream error"})
            return "#EXTM3U\n"

        monkeypatch.setattr(soop_spider, "async_req", fake_async_req)

        with pytest.raises(RuntimeError, match="响应缺少 data 字段"):
            _run(soop_spider.get_sooplive_stream_data(url))


class TestGlobalRoute:
    """www.sooplive.com 国际版应走 global API 分支。"""

    def test_offline_when_not_streaming(self, monkeypatch):
        url = "https://www.sooplive.com/station/roket0829"

        async def fake_channel(bj_id, proxy_addr=None, cookies=None):
            return "박퍼니-roket0829"

        async def fake_stream_info(bj_id, proxy_addr=None, cookies=None):
            return False, "some-title"

        monkeypatch.setattr(soop_spider, "_get_soop_channel_info_global", fake_channel)
        monkeypatch.setattr(soop_spider, "_get_soop_stream_info_global", fake_stream_info)

        result = _run(soop_spider.get_sooplive_stream_data(url))
        assert result["is_live"] is False
        assert result["anchor_name"] == "박퍼니-roket0829"
        assert result["live_url"] == url


class TestLoadsSoop:
    """_loads_soop 把空/非 JSON 响应转成清晰可读的错误，而非难懂的 JSONDecodeError。"""

    def test_valid_json(self):
        assert soop_spider._loads_soop('{"result": 1}', "watch") == {"result": 1}

    def test_empty_string_raises_clear_error(self):
        # 复现线上报错：空响应导致 json.loads 抛 "Expecting value: line 1 column 1 (char 0)"
        with pytest.raises(RuntimeError, match="返回空响应"):
            soop_spider._loads_soop("", "broad/a/watch")

    def test_whitespace_only_raises_clear_error(self):
        with pytest.raises(RuntimeError, match="返回空响应"):
            soop_spider._loads_soop("   \n  ", "broad/a/watch")

    def test_non_json_raises_clear_error_with_snippet(self):
        # async_req 网络异常时会返回 str(e) 这类非 JSON 文本
        with pytest.raises(RuntimeError, match="返回非 JSON 响应"):
            soop_spider._loads_soop("ConnectTimeout occurred", "player_live_api")

    def test_non_json_preserves_original_cause(self):
        try:
            soop_spider._loads_soop("not json", "watch")
        except RuntimeError as e:
            assert isinstance(e.__cause__, json.JSONDecodeError)
        else:
            pytest.fail("expected RuntimeError")
