# -*- encoding: utf-8 -*-
"""监控时间窗口模块。

提供时间窗口配置的解析、校验和判断功能。
支持按日/周/月/自定义周期控制监控任务的启停时间。

配置格式（config.ini [录制设置] 段）：
    监控时间窗口开启(是/否) = 否
    监控开始时间(HH:MM) = 08:00
    监控结束时间(HH:MM) = 23:00
    监控重复周期(每天/每周/每月/自定义) = 每天
    监控生效星期(1-7逗号分隔) = 1,2,3,4,5,6,7
    监控生效日期(1-31逗号分隔) = 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass
class TimeWindowConfig:
    """监控时间窗口配置数据类。"""
    enabled: bool = False
    start_time: str = "00:00"
    end_time: str = "23:59"
    repeat_cycle: str = "每天"  # 每天/每周/每月/自定义
    weekdays: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7])
    monthdays: list[int] = field(default_factory=lambda: list(range(1, 32)))


def parse_time(time_str: str) -> tuple[int, int] | None:
    """将 HH:MM 格式时间字符串解析为 (hour, minute) 元组。

    Args:
        time_str: 格式为 "HH:MM" 的时间字符串

    Returns:
        解析成功返回 (hour, minute)，格式错误返回 None
    """
    time_str = time_str.strip()
    if ':' not in time_str:
        return None
    parts = time_str.split(':')
    if len(parts) != 2:
        return None
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def parse_int_list(text: str, min_val: int, max_val: int) -> list[int]:
    """将逗号分隔的整数字符串解析为整数列表，过滤超范围的值。

    Args:
        text: 如 "1,2,3,5,7"
        min_val: 允许的最小值（含）
        max_val: 允许的最大值（含）

    Returns:
        过滤后的有序整数列表
    """
    result = []
    for item in text.replace('，', ',').split(','):
        item = item.strip()
        if not item:
            continue
        try:
            val = int(item)
            if min_val <= val <= max_val:
                result.append(val)
        except ValueError:
            continue
    return sorted(set(result))


def validate_config(config: TimeWindowConfig) -> tuple[bool, str]:
    """校验时间窗口配置的合法性。

    Returns:
        (is_valid, error_message) — 合法时 error_message 为空字符串
    """
    start = parse_time(config.start_time)
    if start is None:
        return False, f"监控开始时间格式错误: '{config.start_time}'，应为 HH:MM"

    end = parse_time(config.end_time)
    if end is None:
        return False, f"监控结束时间格式错误: '{config.end_time}'，应为 HH:MM"

    # 允许跨天配置（如 22:00 - 06:00），但不允许起止时间完全相同
    if start == end:
        return False, "监控开始时间与结束时间不能相同"

    if config.repeat_cycle == "每周" and not config.weekdays:
        return False, "每周模式下必须指定至少一个生效星期"

    if config.repeat_cycle == "每月" and not config.monthdays:
        return False, "每月模式下必须指定至少一个生效日期"

    return True, ""


def is_within_window(config: TimeWindowConfig,
                     now: datetime.datetime | None = None) -> bool:
    """判断当前时刻是否在监控时间窗口内。

    规则：
    - 若功能未开启（enabled=False），始终返回 True（不限制）
    - 先判断当前日期是否匹配重复周期（每天/每周/每月/自定义）
    - 再判断当前时刻是否在 [start_time, end_time) 范围内
    - 支持跨天配置（如 start=22:00, end=06:00 表示晚10点到次日早6点）

    Args:
        config: 时间窗口配置
        now: 当前时间（默认取 datetime.datetime.now()，方便测试注入）

    Returns:
        True 表示在窗口内（应正常监控），False 表示在窗口外（应暂停监控）
    """
    if not config.enabled:
        return True

    if now is None:
        now = datetime.datetime.now()

    # 检查日期是否在周期内
    if not _is_date_in_cycle(config, now):
        return False

    # 检查时间是否在窗口内
    return _is_time_in_range(config, now)


def _is_date_in_cycle(config: TimeWindowConfig, now: datetime.datetime) -> bool:
    """检查当前日期是否匹配指定的重复周期。"""
    cycle = config.repeat_cycle.strip()

    if cycle == "每天":
        return True

    if cycle == "每周":
        # Python isoweekday(): Monday=1, Sunday=7
        return now.isoweekday() in config.weekdays

    if cycle == "每月":
        return now.day in config.monthdays

    if cycle == "自定义":
        # 自定义模式：同时检查星期和日期，两者都满足才生效
        return now.isoweekday() in config.weekdays and now.day in config.monthdays

    # 未识别的周期类型，按"每天"处理
    return True


def _is_time_in_range(config: TimeWindowConfig, now: datetime.datetime) -> bool:
    """检查当前时刻是否在 [start_time, end_time) 内，支持跨天。"""
    start = parse_time(config.start_time)
    end = parse_time(config.end_time)
    if start is None or end is None:
        return True  # 配置错误时不限制

    start_minutes = start[0] * 60 + start[1]
    end_minutes = end[0] * 60 + end[1]
    now_minutes = now.hour * 60 + now.minute

    if start_minutes <= end_minutes:
        # 同日窗口：如 08:00 - 23:00
        return start_minutes <= now_minutes < end_minutes
    else:
        # 跨天窗口：如 22:00 - 06:00（包含午夜）
        return now_minutes >= start_minutes or now_minutes < end_minutes


def seconds_until_next_window_open(config: TimeWindowConfig,
                                   now: datetime.datetime | None = None) -> float:
    """计算距离下一次监控窗口开启的秒数。

    Args:
        config: 时间窗口配置
        now: 当前时间（默认取系统当前时间）

    Returns:
        - 若功能未开启或当前已在窗口内：返回 0
        - 否则返回距离下一次窗口开启的秒数（>= 1）

    实现策略：
        以日为粒度，从今天起向后枚举最多 366 天，
        找到第一个"日期匹配周期 + start_time 之后或当天"的时间点。
    """
    if not config.enabled:
        return 0.0
    if now is None:
        now = datetime.datetime.now()

    # 已在窗口内 → 立即返回
    if is_within_window(config, now):
        return 0.0

    start = parse_time(config.start_time)
    if start is None:
        return 0.0  # 配置错误时不延迟

    start_hour, start_minute = start
    today = now.date()

    # 向后扫描最多 400 天，覆盖每月 31 号、每周等所有边界
    for offset in range(0, 400):
        candidate_date = today + datetime.timedelta(days=offset)
        candidate_dt = datetime.datetime.combine(
            candidate_date,
            datetime.time(start_hour, start_minute),
        )

        # 候选时间必须在 now 之后
        if candidate_dt <= now:
            continue

        # 候选日期必须满足重复周期
        if not _is_date_in_cycle(config, candidate_dt):
            continue

        # 跨天窗口的特殊情况：start>end 时 candidate_dt 即窗口起点，OK
        # 同日窗口：直接使用 candidate_dt
        return (candidate_dt - now).total_seconds()

    # 理论上不会到达，兜底返回一个合理值
    return 86400.0

