# -*- encoding: utf-8 -*-
"""Tests for :mod:`src.app.naming` - pure helper functions."""
import pytest

from src.app import naming, state


def test_get_quality_code_known():
    assert naming.get_quality_code("原画") == "OD"
    assert naming.get_quality_code("超清") == "UHD"
    assert naming.get_quality_code("流畅") == "LD"


def test_get_quality_code_unknown_returns_none():
    assert naming.get_quality_code("未知") is None
    assert naming.get_quality_code("") is None


def test_clean_name_strips_special_chars(monkeypatch):
    monkeypatch.setattr(state, "clean_emoji", False)
    assert naming.clean_name("Hello/World") == "Hello_World"
    assert naming.clean_name("（test）") == "(test)"


def test_clean_name_falls_back_for_empty(monkeypatch):
    monkeypatch.setattr(state, "clean_emoji", False)
    assert naming.clean_name("   ") == "空白昵称"
    assert naming.clean_name("***") == "空白昵称"


def test_get_record_headers_known_platform():
    h = naming.get_record_headers("WinkTV", "https://www.winktv.co.kr/foo")
    assert h.startswith("origin:")


def test_get_record_headers_shopee_uses_domain():
    h = naming.get_record_headers("shopee", "https://live.shopee.tw/abc/def")
    assert h == "origin:https://live.shopee.tw"


def test_get_record_headers_unknown_returns_none():
    assert naming.get_record_headers("不存在的平台", "https://x.y") is None


def test_is_flv_preferred_platform():
    assert naming.is_flv_preferred_platform("https://live.douyin.com/123")
    assert naming.is_flv_preferred_platform("https://www.tiktok.com/@u/live")
    assert not naming.is_flv_preferred_platform("https://www.huya.com/12345")


def test_select_source_url_prefers_flv_for_douyin():
    info = {"flv_url": "https://x/y.flv?codec=avc", "record_url": "https://x/y.m3u8"}
    assert naming.select_source_url("https://live.douyin.com/1", info) == info["flv_url"]


def test_select_source_url_falls_back_for_h265():
    info = {"flv_url": "https://x/y.flv?codec=h265", "record_url": "https://x/y.m3u8"}
    assert naming.select_source_url("https://live.douyin.com/1", info) == info["record_url"]


def test_select_source_url_non_flv_platform():
    info = {"flv_url": "https://x/y.flv", "record_url": "https://x/y.m3u8"}
    assert naming.select_source_url("https://www.huya.com/1", info) == info["record_url"]


def test_contains_url():
    assert naming.contains_url("https://live.douyin.com/123")
    assert naming.contains_url("live.bilibili.com/12345")
    assert not naming.contains_url("just plain text")
