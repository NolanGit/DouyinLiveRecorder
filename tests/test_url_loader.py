# -*- encoding: utf-8 -*-
"""Tests for :mod:`src.app.url_loader` (URL config parsing)."""
import os

import pytest

from src.app import state, url_loader


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch, tmp_path):
    """Isolate ``state.url_tuples_list``/``url_comments``/``need_update_line_list``."""
    monkeypatch.setattr(state, "url_tuples_list", set())
    monkeypatch.setattr(state, "url_comments", [])
    monkeypatch.setattr(state, "need_update_line_list", [])
    monkeypatch.setattr(state, "text_no_repeat_url", [])
    monkeypatch.setattr(state, "video_record_quality", "原画")
    # 重置文件缓存指纹，避免测试间相互影响
    monkeypatch.setattr(state, "url_config_mtime", 0.0)
    monkeypatch.setattr(state, "url_config_size", -1)


def _write(tmp_path, content):
    p = tmp_path / "URL_config.ini"
    p.write_text(content, encoding=state.text_encoding)
    return str(p)


def test_parse_basic_url(monkeypatch, tmp_path):
    path = _write(tmp_path, "https://live.douyin.com/123456789\n")
    monkeypatch.setattr(state, "url_config_file", path)
    url_loader.parse_url_config()
    assert state.text_no_repeat_url
    quality, url, name = state.text_no_repeat_url[0]
    assert quality == "原画"
    assert "live.douyin.com" in url


def test_parse_url_with_quality_and_name(monkeypatch, tmp_path):
    path = _write(tmp_path, "高清,https://live.douyin.com/12345678,主播: foo\n")
    monkeypatch.setattr(state, "url_config_file", path)
    url_loader.parse_url_config()
    assert state.text_no_repeat_url
    quality, url, name = state.text_no_repeat_url[0]
    assert quality == "高清"
    assert "live.douyin.com" in url


def test_comment_line_goes_to_url_comments(monkeypatch, tmp_path):
    path = _write(tmp_path, "#https://live.douyin.com/12345678\n")
    monkeypatch.setattr(state, "url_config_file", path)
    url_loader.parse_url_config()
    assert state.url_comments
    assert any("douyin" in u for u in state.url_comments)
    assert not state.text_no_repeat_url


def test_unknown_host_skipped(monkeypatch, tmp_path):
    path = _write(tmp_path, "https://example.com/some-channel-100\n")
    monkeypatch.setattr(state, "url_config_file", path)
    url_loader.parse_url_config()
    assert not state.text_no_repeat_url


def test_mtime_cache_skips_unchanged_file(monkeypatch, tmp_path):
    """文件未变化时应跳过解析（性能优化）。"""
    path = _write(tmp_path, "https://live.douyin.com/123456789\n")
    monkeypatch.setattr(state, "url_config_file", path)

    # 首次解析
    url_loader.parse_url_config()
    first_count = len(state.text_no_repeat_url)
    first_mtime = state.url_config_mtime
    assert first_count == 1
    assert first_mtime > 0

    # 第二次：文件未变 → 应跳过解析（mtime 不变）
    url_loader.parse_url_config()
    assert state.url_config_mtime == first_mtime


def test_mtime_cache_invalidated_on_file_change(monkeypatch, tmp_path):
    """文件变化后应重新解析。"""
    import time as _time
    path = _write(tmp_path, "https://live.douyin.com/123456789\n")
    monkeypatch.setattr(state, "url_config_file", path)

    url_loader.parse_url_config()
    first_mtime = state.url_config_mtime

    # 等待 mtime 粒度（macOS HFS+ 是 1 秒，APFS 是纳秒级）
    _time.sleep(0.01)
    # 修改文件
    with open(path, 'w', encoding=state.text_encoding) as f:
        f.write("https://live.douyin.com/123456789\n"
                "https://www.huya.com/567890\n")

    url_loader.parse_url_config()
    # 文件变化后应重新解析，mtime 更新
    assert state.url_config_mtime != first_mtime
    assert len(state.text_no_repeat_url) == 2
