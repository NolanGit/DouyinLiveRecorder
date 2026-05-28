# -*- encoding: utf-8 -*-
"""Tests for src.app.config — configuration loading logic."""
import configparser
import os
import tempfile
import pytest


@pytest.fixture
def config_env(tmp_path, monkeypatch):
    """创建临时配置文件并将 state 指向它。"""
    from src.app import state
    config_file = tmp_path / "config" / "config.ini"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("", encoding="utf-8-sig")
    monkeypatch.setattr(state, "config_file", str(config_file))
    monkeypatch.setattr(state, "text_encoding", "utf-8-sig")
    return config_file


class TestReadConfigValue:
    """read_config_value 应正确读取和创建配置项。"""

    def test_returns_default_when_missing(self, config_env):
        from src.app.config import read_config_value
        config = configparser.RawConfigParser()
        result = read_config_value(config, '录制设置', '测试选项', "默认值")
        assert result == "默认值"

    def test_writes_default_to_file_when_missing(self, config_env):
        from src.app.config import read_config_value
        config = configparser.RawConfigParser()
        read_config_value(config, '录制设置', '新选项', "hello")
        # 重新读取文件验证已写入
        config2 = configparser.RawConfigParser()
        config2.read(str(config_env), encoding="utf-8-sig")
        assert config2.get('录制设置', '新选项') == "hello"

    def test_returns_existing_value(self, config_env):
        from src.app.config import read_config_value
        # 先写入一个值
        config_env.write_text(
            "[录制设置]\n已有选项 = 已有值\n", encoding="utf-8-sig"
        )
        config = configparser.RawConfigParser()
        result = read_config_value(config, '录制设置', '已有选项', "默认")
        assert result == "已有值"

    def test_creates_all_required_sections(self, config_env):
        """首次读取时应自动创建所有必要 section。"""
        from src.app.config import read_config_value
        config = configparser.RawConfigParser()
        read_config_value(config, '推送配置', 'test_key', "val")
        expected_sections = ['录制设置', '推送配置', 'Cookie', 'Authorization', '账号密码']
        for sec in expected_sections:
            assert sec in config.sections()


class TestLoad:
    """config.load() 应将配置值正确写入 state。"""

    def test_load_sets_video_save_type(self, config_env, monkeypatch):
        from src.app import config as config_mod, state
        # 写入一个合法的保存格式
        config_env.write_text(
            "[录制设置]\n视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = mkv\n",
            encoding="utf-8-sig",
        )
        config_mod.load()
        assert state.video_save_type == "MKV"

    def test_load_defaults_to_ts_for_invalid_type(self, config_env, monkeypatch):
        from src.app import config as config_mod, state
        config_env.write_text(
            "[录制设置]\n视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = invalid_format\n",
            encoding="utf-8-sig",
        )
        config_mod.load()
        assert state.video_save_type == "TS"

    def test_load_parses_max_request_as_int(self, config_env):
        from src.app import config as config_mod, state
        config_env.write_text(
            "[录制设置]\n同一时间访问网络的线程数 = 5\n",
            encoding="utf-8-sig",
        )
        config_mod.load()
        assert state.max_request == 5

    def test_load_proxy_platform_list_split(self, config_env):
        from src.app import config as config_mod, state
        config_env.write_text(
            "[录制设置]\n使用代理录制的平台(逗号分隔) = tiktok, twitch, youtube\n"
            "是否使用代理ip(是/否) = 是\n",
            encoding="utf-8-sig",
        )
        config_mod.load()
        # split 后各元素可能带前导空格，验证 strip 后的值
        stripped = [s.strip() for s in state.enable_proxy_platform_list]
        assert "tiktok" in stripped
        assert "twitch" in stripped
