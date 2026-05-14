# -*- encoding: utf-8 -*-
"""Tests for :mod:`src.app.proxy_resolver`."""
from src.app import proxy_resolver, state


def _reset(monkeypatch, *, use_proxy=True, addr="http://1.2.3.4:8080",
           enable_list=("tiktok", "soop"), extra=None):
    monkeypatch.setattr(state, "use_proxy", use_proxy)
    monkeypatch.setattr(state, "proxy_addr_bak", addr)
    monkeypatch.setattr(state, "enable_proxy_platform_list", list(enable_list) if enable_list else None)
    monkeypatch.setattr(state, "extra_enable_proxy_platform_list", list(extra) if extra else None)


def test_returns_none_if_stage_disabled(monkeypatch):
    _reset(monkeypatch)
    assert proxy_resolver.get_stage_proxy_address("https://x.tiktok.com/", False) is None


def test_returns_none_if_use_proxy_off(monkeypatch):
    _reset(monkeypatch, use_proxy=False)
    assert proxy_resolver.get_stage_proxy_address("https://x.tiktok.com/", True) is None


def test_returns_none_when_no_addr_configured(monkeypatch):
    _reset(monkeypatch, addr="")
    assert proxy_resolver.get_stage_proxy_address("https://x.tiktok.com/", True) is None


def test_returns_addr_when_url_in_enable_list(monkeypatch):
    _reset(monkeypatch)
    assert proxy_resolver.get_stage_proxy_address("https://www.tiktok.com/", True) == "http://1.2.3.4:8080"


def test_returns_addr_when_url_only_in_extra(monkeypatch):
    _reset(monkeypatch, enable_list=("none",), extra=("kuaishou",))
    assert proxy_resolver.get_stage_proxy_address("https://www.kuaishou.com/", True) == "http://1.2.3.4:8080"


def test_returns_none_when_url_unmatched(monkeypatch):
    _reset(monkeypatch)
    assert proxy_resolver.get_stage_proxy_address("https://www.huya.com/1", True) is None
