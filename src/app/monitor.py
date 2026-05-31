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


def display_info() -> None:
    """Print a periodic dashboard summarising current monitor / record status."""
    time.sleep(5)
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

            if Path(sys.executable).name != 'pythonw.exe':
                os.system(state.clear_command)
            print(f"\r共监测{state.monitoring}个直播中", end=" | ")
            print(f"同一时间访问网络的线程数: {state.max_request}", end=" | ")
            print(
                f"监控是否使用代理: {'是' if state.use_proxy and state.use_proxy_for_monitoring else '否'}",
                end=" | ",
            )
            print(
                f"录制是否使用代理: {'是' if state.use_proxy and state.use_proxy_for_recording else '否'}",
                end=" | ",
            )
            if state.split_video_by_time:
                print(f"录制分段开启: {state.split_time}秒", end=" | ")
            else:
                print("录制分段开启: 否", end=" | ")
            if state.create_time_file:
                print("是否生成时间文件: 是", end=" | ")
            print(f"录制视频质量为: {state.video_record_quality}", end=" | ")
            print(f"录制视频格式为: {state.video_save_type}", end=" | ")
            print(f"目前瞬时错误数为: {state.error_count}", end=" | ")
            now = time.strftime("%H:%M:%S", time.localtime())
            print(f"当前时间: {now}")

            if len(state.recording) == 0:
                time.sleep(5)
                if state.monitoring == 0:
                    print("\r没有正在监测和录制的直播")
                else:
                    print(f"\r没有正在录制的直播 循环监测间隔时间：{state.delay_default}秒")
            else:
                now_time = datetime.datetime.now()
                print("x" * 60)
                no_repeat_recording = list(set(state.recording))
                print(f"正在录制{len(no_repeat_recording)}个直播: ")
                for recording_live in no_repeat_recording:
                    rt, qa = state.recording_time_list[recording_live]
                    have_record_time = now_time - rt
                    print(f"{recording_live}[{qa}] 正在录制中 {str(have_record_time).split('.')[0]}")
                print("x" * 60)
                state.start_display_time = now_time
        except Exception as e:  # noqa: BLE001
            logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")


def adjust_max_request() -> None:
    """Dynamically scale ``state.max_request`` based on the recent error rate."""
    preset = state.max_request
    while True:
        time.sleep(5)
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
