# -*- encoding: utf-8 -*-
"""Status display and dynamic ``max_request`` adjustment threads."""
from __future__ import annotations

import datetime
import os
import sys
import time
from pathlib import Path

from src.utils import logger

from . import state
from .time_window import TimeWindowConfig, is_within_window, seconds_until_next_window_open


def _build_time_window_config() -> TimeWindowConfig:
    """构建当前时间窗口配置对象。"""
    return TimeWindowConfig(
        enabled=state.time_window_enabled,
        start_time=state.time_window_start,
        end_time=state.time_window_end,
        repeat_cycle=state.time_window_cycle,
        weekdays=state.time_window_weekdays,
        monthdays=state.time_window_monthdays,
    )


def _is_in_monitoring_window() -> bool:
    """检查当前是否在监控时间窗口内。"""
    if not state.time_window_enabled:
        return True
    return is_within_window(_build_time_window_config())


def _clear_screen() -> None:
    """清屏。

    优化前: ``os.system(state.clear_command)`` 每次 fork 一个 clear/cls 子进程。
    优化后: 直接写 ANSI escape sequence。在 Windows 上若不支持 ANSI 则降级。
    """
    # 大多数现代终端（含 Win10+ 的 cmd/powershell）都支持 ANSI escape
    if state.os_type != 'nt':
        sys.stdout.write('\033[H\033[J')
        sys.stdout.flush()
        return
    # Windows 兼容性兜底（py 3.10 在 Win10+ 默认开启 ANSI）
    try:
        sys.stdout.write('\033[H\033[J')
        sys.stdout.flush()
    except OSError:
        os.system(state.clear_command)


def display_info() -> None:
    """Print a periodic dashboard summarising current monitor / record status.

    优化策略：
    - 配置摘要行（max_request / 代理 / 分段 / 质量 / 格式 / 间隔等）只在变化时刷新
    - 录制中：每 5 秒刷新进度（时间在变化）
    - 完全空闲：每分钟刷新一次心跳
    """
    time.sleep(5)
    last_summary: str | None = None
    last_idle_heartbeat: float = 0.0
    while True:
        try:
            sys.stdout.flush()
            time.sleep(5)

            # 时间窗口外：精确休眠到下一次窗口开启，避免无意义的 dashboard 刷新
            if not _is_in_monitoring_window():
                secs = seconds_until_next_window_open(_build_time_window_config())
                if secs > 0:
                    time.sleep(secs)
                continue

            # 构建当前的配置摘要快照（不含变动的「时间/错误数」字段）
            summary_parts = [
                f"共监测{state.monitoring}个直播中",
                f"同一时间访问网络的线程数: {state.max_request}",
                f"监控是否使用代理: {'是' if state.use_proxy and state.use_proxy_for_monitoring else '否'}",
                f"录制是否使用代理: {'是' if state.use_proxy and state.use_proxy_for_recording else '否'}",
            ]
            if state.split_video_by_time:
                summary_parts.append(f"录制分段开启: {state.split_time}秒")
            else:
                summary_parts.append("录制分段开启: 否")
            if state.create_time_file:
                summary_parts.append("是否生成时间文件: 是")
            summary_parts.append(f"录制视频质量为: {state.video_record_quality}")
            summary_parts.append(f"录制视频格式为: {state.video_save_type}")
            summary_parts.append(f"循环监测间隔: {state.delay_default}秒")
            current_summary = " | ".join(summary_parts)

            recording_count = len(state.recording)
            now_ts = time.time()

            # 决定是否刷新输出：
            # 1. 配置摘要变化（max_request / 代理开关 / 录制数等）
            # 2. 正在录制：每 5 秒刷新一次（时间进度需要更新）
            # 3. 完全空闲（无录制）：每 60 秒输出一次心跳
            should_refresh = False
            if current_summary != last_summary:
                should_refresh = True
            elif recording_count > 0:
                should_refresh = True
            elif now_ts - last_idle_heartbeat >= 60:
                should_refresh = True

            if not should_refresh:
                continue

            if Path(sys.executable).name != 'pythonw.exe':
                _clear_screen()
            now = time.strftime("%H:%M:%S", time.localtime())
            print(
                f"\r{current_summary} | "
                f"目前瞬时错误数为: {state.error_count} | 当前时间: {now}"
            )
            last_summary = current_summary

            if recording_count == 0:
                last_idle_heartbeat = now_ts
                if state.monitoring == 0:
                    print("\r没有正在监测和录制的直播")
                else:
                    print("\r没有正在录制的直播")
            else:
                now_time = datetime.datetime.now()
                print("-" * 60)
                no_repeat_recording = list(set(state.recording))
                print(f"正在录制{len(no_repeat_recording)}个直播: ")
                for recording_live in no_repeat_recording:
                    info = state.recording_time_list[recording_live]
                    rt, qa = info[0], info[1]
                    # 兼容历史记录可能没有第 3 项 proxy 信息
                    proxy_addr = info[2] if len(info) > 2 else None
                    have_record_time = now_time - rt
                    proxy_tag = f"代理: {proxy_addr}" if proxy_addr else "代理: 直连"
                    # recording_live 本身已包含「序号X」前缀（来自 recorder.py 的 record_name）
                    print(
                        f"{recording_live}[{qa}] [{proxy_tag}] "
                        f"正在录制中 {str(have_record_time).split('.')[0]}"
                    )
                print("-" * 60)
                state.start_display_time = now_time
        except Exception as e:  # noqa: BLE001
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")


def adjust_max_request() -> None:
    """Dynamically scale ``state.max_request`` based on the recent error rate.

    窗口外不需要进行调节（无 IO 错误产生），精确休眠到下次窗口开启。
    """
    preset = state.max_request
    while True:
        time.sleep(5)

        # 时间窗口外：精确休眠到下一次窗口开启，避免空转
        if not _is_in_monitoring_window():
            secs = seconds_until_next_window_open(_build_time_window_config())
            if secs > 0:
                time.sleep(secs)
            continue

        with state.max_request_lock:
            if state.error_window:
                error_rate = sum(state.error_window) / len(state.error_window)
            else:
                error_rate = 0

            if error_rate > state.error_threshold:
                state.max_request = max(1, state.max_request - 1)
            elif error_rate < state.error_threshold / 2 and state.max_request < preset:
                state.max_request += 1

            if state.pre_max_request != state.max_request:
                state.pre_max_request = state.max_request
                print(f"\r同一时间访问网络的线程数动态改为 {state.max_request}")

        state.error_window.append(state.error_count)
        if len(state.error_window) > state.error_window_size:
            state.error_window.pop(0)
        state.error_count = 0
