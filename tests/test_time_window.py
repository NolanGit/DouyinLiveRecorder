# -*- encoding: utf-8 -*-
"""Tests for src.app.time_window — 监控时间窗口功能。"""
import datetime
import pytest

from src.app.time_window import (
    TimeWindowConfig,
    is_within_window,
    parse_int_list,
    parse_time,
    validate_config,
    _is_date_in_cycle,
    _is_time_in_range,
)


# ──────────────────────────────────────────────────────────────────────────────
# parse_time
# ──────────────────────────────────────────────────────────────────────────────

class TestParseTime:
    def test_valid_time(self):
        assert parse_time("08:30") == (8, 30)

    def test_midnight(self):
        assert parse_time("00:00") == (0, 0)

    def test_end_of_day(self):
        assert parse_time("23:59") == (23, 59)

    def test_with_spaces(self):
        assert parse_time("  09:05  ") == (9, 5)

    def test_invalid_no_colon(self):
        assert parse_time("0830") is None

    def test_invalid_hour_out_of_range(self):
        assert parse_time("25:00") is None

    def test_invalid_minute_out_of_range(self):
        assert parse_time("12:60") is None

    def test_invalid_non_numeric(self):
        assert parse_time("ab:cd") is None

    def test_invalid_too_many_colons(self):
        assert parse_time("08:30:00") is None

    def test_empty_string(self):
        assert parse_time("") is None


# ──────────────────────────────────────────────────────────────────────────────
# parse_int_list
# ──────────────────────────────────────────────────────────────────────────────

class TestParseIntList:
    def test_normal_list(self):
        assert parse_int_list("1,3,5,7", 1, 7) == [1, 3, 5, 7]

    def test_filters_out_of_range(self):
        assert parse_int_list("0,1,2,8,9", 1, 7) == [1, 2]

    def test_deduplicates_and_sorts(self):
        assert parse_int_list("5,3,5,1,3", 1, 7) == [1, 3, 5]

    def test_chinese_comma(self):
        assert parse_int_list("1，2，3", 1, 7) == [1, 2, 3]

    def test_empty_string(self):
        assert parse_int_list("", 1, 7) == []

    def test_invalid_entries_skipped(self):
        assert parse_int_list("1,abc,3,!,5", 1, 7) == [1, 3, 5]

    def test_spaces_handled(self):
        assert parse_int_list(" 1 , 2 , 3 ", 1, 7) == [1, 2, 3]

    def test_monthdays(self):
        result = parse_int_list("1,15,28,31,32", 1, 31)
        assert result == [1, 15, 28, 31]


# ──────────────────────────────────────────────────────────────────────────────
# validate_config
# ──────────────────────────────────────────────────────────────────────────────

class TestValidateConfig:
    def test_valid_config(self):
        cfg = TimeWindowConfig(enabled=True, start_time="08:00", end_time="23:00")
        valid, err = validate_config(cfg)
        assert valid is True
        assert err == ""

    def test_invalid_start_time(self):
        cfg = TimeWindowConfig(enabled=True, start_time="25:00", end_time="23:00")
        valid, err = validate_config(cfg)
        assert valid is False
        assert "开始时间格式错误" in err

    def test_invalid_end_time(self):
        cfg = TimeWindowConfig(enabled=True, start_time="08:00", end_time="abc")
        valid, err = validate_config(cfg)
        assert valid is False
        assert "结束时间格式错误" in err

    def test_same_start_end_rejected(self):
        cfg = TimeWindowConfig(enabled=True, start_time="12:00", end_time="12:00")
        valid, err = validate_config(cfg)
        assert valid is False
        assert "不能相同" in err

    def test_cross_day_allowed(self):
        """跨天配置（如22:00-06:00）应合法。"""
        cfg = TimeWindowConfig(enabled=True, start_time="22:00", end_time="06:00")
        valid, err = validate_config(cfg)
        assert valid is True

    def test_weekly_requires_weekdays(self):
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="20:00",
            repeat_cycle="每周", weekdays=[]
        )
        valid, err = validate_config(cfg)
        assert valid is False
        assert "至少一个生效星期" in err

    def test_monthly_requires_monthdays(self):
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="20:00",
            repeat_cycle="每月", monthdays=[]
        )
        valid, err = validate_config(cfg)
        assert valid is False
        assert "至少一个生效日期" in err


# ──────────────────────────────────────────────────────────────────────────────
# is_within_window
# ──────────────────────────────────────────────────────────────────────────────

class TestIsWithinWindow:
    def test_disabled_always_returns_true(self):
        """功能未开启时始终返回 True。"""
        cfg = TimeWindowConfig(enabled=False)
        # 无论什么时间都应返回 True
        assert is_within_window(cfg, datetime.datetime(2025, 1, 1, 3, 0)) is True

    def test_within_same_day_window(self):
        """同日窗口内的时间应返回 True。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每天"
        )
        # 10:30 在 08:00-22:00 内
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 10, 30)) is True

    def test_outside_same_day_window(self):
        """同日窗口外的时间应返回 False。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每天"
        )
        # 23:00 不在 08:00-22:00 内
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 23, 0)) is False
        # 07:00 不在 08:00-22:00 内
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 7, 0)) is False

    def test_cross_day_window_late_night(self):
        """跨天窗口（22:00-06:00），午夜后应在窗口内。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="22:00", end_time="06:00",
            repeat_cycle="每天"
        )
        # 23:30 在窗口内
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 23, 30)) is True
        # 03:00 在窗口内
        assert is_within_window(cfg, datetime.datetime(2025, 6, 2, 3, 0)) is True
        # 12:00 不在窗口内
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 12, 0)) is False

    def test_boundary_start_time_included(self):
        """开始时间边界应包含在内。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每天"
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 8, 0)) is True

    def test_boundary_end_time_excluded(self):
        """结束时间边界应不包含（左闭右开）。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每天"
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 1, 22, 0)) is False

    def test_weekly_matching_day(self):
        """每周模式：匹配的星期几应在窗口内。"""
        # 2025-06-02 是星期一 (isoweekday=1)
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每周", weekdays=[1, 3, 5]
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 2, 10, 0)) is True

    def test_weekly_non_matching_day(self):
        """每周模式：不匹配的星期几应返回 False。"""
        # 2025-06-03 是星期二 (isoweekday=2)
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每周", weekdays=[1, 3, 5]
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 3, 10, 0)) is False

    def test_monthly_matching_day(self):
        """每月模式：匹配日期应在窗口内。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每月", monthdays=[1, 15, 28]
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 15, 12, 0)) is True

    def test_monthly_non_matching_day(self):
        """每月模式：不匹配日期应返回 False。"""
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="每月", monthdays=[1, 15, 28]
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 10, 12, 0)) is False

    def test_custom_requires_both_weekday_and_monthday(self):
        """自定义模式：需同时满足星期和日期条件。"""
        # 2025-06-02 是星期一，且日期=2
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="自定义", weekdays=[1], monthdays=[2]
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 2, 10, 0)) is True

    def test_custom_weekday_not_match(self):
        """自定义模式：星期不匹配则返回 False。"""
        # 2025-06-03 是星期二，日期=3
        cfg = TimeWindowConfig(
            enabled=True, start_time="08:00", end_time="22:00",
            repeat_cycle="自定义", weekdays=[1], monthdays=[3]
        )
        assert is_within_window(cfg, datetime.datetime(2025, 6, 3, 10, 0)) is False

    def test_uses_current_time_when_none(self):
        """now=None 时应使用当前系统时间（不抛异常）。"""
        cfg = TimeWindowConfig(enabled=True, start_time="00:00", end_time="23:59")
        # 只验证不抛异常
        result = is_within_window(cfg)
        assert isinstance(result, bool)


# ──────────────────────────────────────────────────────────────────────────────
# 向后兼容性
# ──────────────────────────────────────────────────────────────────────────────

class TestBackwardCompatibility:
    """验证功能不影响现有逻辑（默认配置下不限制）。"""

    def test_default_config_always_allows(self):
        """默认配置（enabled=False）下任何时间都允许。"""
        cfg = TimeWindowConfig()  # 全部默认值
        for hour in range(24):
            dt = datetime.datetime(2025, 6, 1, hour, 30)
            assert is_within_window(cfg, dt) is True

    def test_state_defaults_disabled(self):
        """state 中默认值应为 disabled。"""
        from src.app import state
        assert state.time_window_enabled is False
