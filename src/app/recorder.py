# -*- encoding: utf-8 -*-
"""Per-URL recording loop.

Each URL spawns a daemon thread that runs :func:`start_record`. The function
delegates platform-specific URL handling to :mod:`platform_dispatch`, ffmpeg
command construction & per-format pipelines to :mod:`recorder_pipeline`, and
notification to :mod:`notifier`.
"""
from __future__ import annotations

import datetime
import random
import subprocess
import threading
import time

from src.utils import logger
from src import utils

from . import state
from .ffmpeg_runner import clear_record_info
from .naming import (
    clean_name, get_quality_code, is_flv_preferred_platform, select_source_url,
)
from .notifier import push_message
from .platform_dispatch import UnknownPlatformError, dispatch
from .proxy_resolver import get_stage_proxy_address
from .recorder_pipeline import (
    build_ffmpeg_base, build_save_path, record_audio,
    record_flv_direct, record_with_format,
)
from .time_window import TimeWindowConfig, is_within_window


def _is_monitoring_allowed() -> bool:
    """检查当前是否在监控时间窗口内。

    窗口外时录制线程的轮询检测会暂停（sleep），
    但已开始的录制不受影响（由调用方在录制开始前检查）。
    """
    if not state.time_window_enabled:
        return True
    tw_config = TimeWindowConfig(
        enabled=True,
        start_time=state.time_window_start,
        end_time=state.time_window_end,
        repeat_cycle=state.time_window_cycle,
        weekdays=state.time_window_weekdays,
        monthdays=state.time_window_monthdays,
    )
    return is_within_window(tw_config)


def _push_status(record_name: str, record_url: str, message_template: str,
                 fallback: str) -> None:
    """Schedule a non-blocking status push."""
    push_at = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    content = (message_template or fallback) \
        .replace('[直播间名称]', record_name) \
        .replace('[时间]', push_at) \
        .replace(r'\n', '\n')
    threading.Thread(
        target=push_message,
        args=(record_name, record_url, content),
        daemon=True,
    ).start()


def _record_error(exc: Exception) -> None:
    logger.error(f"错误信息: {exc} 发生错误的行数: {exc.__traceback__.tb_lineno}")
    with state.max_request_lock:
        state.error_count += 1
        state.error_window.append(1)


def _resolve_anchor_name(stored_name: str, port_info: dict) -> str:
    """Determine anchor display name from URL_config or spider response."""
    if stored_name:
        if '主播:' in stored_name:
            tail = stored_name.split('主播:', 1)[1].strip()
            if tail:
                return tail
        return port_info.get("anchor_name", '')
    return port_info.get("anchor_name", '')


def _calculate_record_save_type(record_url: str, port_info: dict) -> str:
    """FLV preferred platforms must fall back to TS for h265 streams."""
    record_save_type = state.video_save_type
    if is_flv_preferred_platform(record_url) and port_info.get('flv_url'):
        codec = utils.get_query_params(port_info['flv_url'], "codec")
        if codec and codec[0] == 'h265':
            logger.warning("FLV is not supported for h265 codec, use TS format instead")
            record_save_type = "TS"
    return record_save_type


def _live_started(port_info: dict, platform: str, record_url: str,
                  record_quality_zh: str, record_name: str, anchor_name: str,
                  record_proxy_address: str | None) -> tuple[bool, bool]:
    """Run the actual recording for an in-progress live. Returns (return_thread, finished)."""
    real_url = select_source_url(record_url, port_info)
    if not real_url:
        return False, False

    now = datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
    full_path, title_in_name = build_save_path(platform, anchor_name, port_info, now)

    if platform != '自定义录制直播':
        if state.enable_https_recording and real_url.startswith("http://"):
            real_url = real_url.replace("http://", "https://")
        if platform in ('shopee', 'migu'):
            real_url = real_url.replace("https://", "http://")

    ffmpeg_command = build_ffmpeg_base(real_url, record_url, platform, record_proxy_address)

    state.recording.add(record_name)
    state.recording_time_list[record_name] = [datetime.datetime.now(), record_quality_zh]
    if state.show_url:
        special = ('WinkTV', 'PandaTV', 'ShowRoom', 'CHZZK', 'Youtube')
        if platform in special:
            logger.info(
                f"{platform} | {anchor_name} | 直播源地址: {port_info.get('m3u8_url')}",
            )
        else:
            logger.info(f"{platform} | {anchor_name} | 直播源地址: {real_url}")

    only_flv_record = platform in ('shopee', '花椒直播')
    only_audio_record = platform in ('猫耳FM直播', 'Look直播')
    record_save_type = _calculate_record_save_type(record_url, port_info)
    if only_flv_record:
        logger.debug(f"提示: {platform} 将强制使用FLV格式录制")

    finished = False
    if only_audio_record or any(i in record_save_type for i in ('MP3', 'M4A')):
        try:
            comment_end = record_audio(
                ffmpeg_command, full_path, anchor_name, title_in_name,
                record_save_type, record_name, record_url, record_proxy_address,
            )
            if comment_end:
                return True, finished
        except subprocess.CalledProcessError as e:
            _record_error(e)
    elif only_flv_record:
        try:
            if record_flv_direct(
                port_info, full_path, anchor_name, title_in_name, now,
                record_quality_zh, record_name, record_url, platform,
                record_proxy_address,
            ):
                finished = True
        except Exception as e:  # noqa: BLE001
            clear_record_info(record_name, record_url)
            state.color_obj.print_colored(
                f"\n{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制出错,请检查网络\n",
                state.color_obj.RED,
            )
            _record_error(e)
    else:
        try:
            comment_end = record_with_format(
                ffmpeg_command, record_save_type, full_path, anchor_name,
                title_in_name, now, record_name, record_url, record_proxy_address,
            )
            if comment_end:
                return True, finished
        except subprocess.CalledProcessError as e:
            _record_error(e)

    return False, finished


def _sleep_until_next_check(anchor_name: str, record_finished: bool, count_time: float) -> None:
    """Wait the configured loop interval, applying error / finish backoff."""
    num = max(0, random.randint(-5, 5) + state.delay_default)
    x = num
    if state.error_count > 20:
        x += 60
        state.color_obj.print_colored("\r瞬时错误太多,延迟加60秒", state.color_obj.YELLOW)

    if record_finished:
        elapsed = time.time() - count_time
        if elapsed < 60:
            x = 30

    while x:
        x -= 1
        if state.loop_time:
            print(f'\r{anchor_name}循环等待{x}秒 ', end="")
        time.sleep(1)
    if state.loop_time:
        print('\r检测直播间中...', end="")


def start_record(url_data: tuple, count_variable: int = -1) -> None:
    """Recorder thread entry. Loops forever for a single URL until commented."""
    while True:
        try:
            record_finished = False
            run_once = False
            start_pushed = False
            new_record_url = ''
            count_time = time.time()
            record_quality_zh, record_url, anchor_name = url_data
            record_quality = get_quality_code(record_quality_zh)
            monitor_proxy_address = get_stage_proxy_address(record_url, state.use_proxy_for_monitoring)
            record_proxy_address = get_stage_proxy_address(record_url, state.use_proxy_for_recording)
            platform = '未知平台'

            while True:
                try:
                    # 时间窗口检查：窗口外暂停轮询，但不退出线程
                    if not _is_monitoring_allowed():
                        time.sleep(30)
                        continue

                    try:
                        platform, port_info, dispatched_new_url = dispatch(
                            record_url, record_quality, monitor_proxy_address,
                        )
                        if dispatched_new_url:
                            new_record_url = dispatched_new_url
                    except UnknownPlatformError:
                        logger.error(f'{record_url} {platform}直播地址')
                        return

                    anchor_name = _resolve_anchor_name(anchor_name, port_info)
                    if not port_info.get("anchor_name", ''):
                        print(
                            f'序号{count_variable} 网址内容获取失败,进行重试中...'
                            f'获取失败的地址是:{url_data}',
                        )
                        with state.max_request_lock:
                            state.error_count += 1
                            state.error_window.append(1)
                    else:
                        anchor_name = clean_name(anchor_name)
                        record_name = f'序号{count_variable} {anchor_name}'

                        if record_url in state.url_comments:
                            print(f"[{anchor_name}]已被注释,本条线程将会退出")
                            clear_record_info(record_name, record_url)
                            return

                        if not url_data[-1] and run_once is False:
                            line_url = new_record_url or record_url
                            state.need_update_line_list.append(
                                f'{record_url}|{line_url},主播: {anchor_name.strip()}',
                            )
                            if new_record_url:
                                state.not_record_list.append(new_record_url)
                            run_once = True

                        if port_info['is_live'] is False:
                            print(f"\r{record_name} 等待直播... ")
                            if start_pushed:
                                if state.over_show_push:
                                    _push_status(
                                        record_name, record_url,
                                        state.over_push_message_text,
                                        "直播间状态更新：[直播间名称] 直播已结束！时间：[时间]",
                                    )
                                start_pushed = False
                        else:
                            print(f"\r{record_name} 正在直播中...")

                            if state.live_status_push and not start_pushed:
                                if state.begin_show_push:
                                    _push_status(
                                        record_name, record_url,
                                        state.begin_push_message_text,
                                        "直播间状态更新：[直播间名称] 正在直播中，时间：[时间]",
                                    )
                                start_pushed = True

                            if state.disable_record:
                                time.sleep(state.push_check_seconds)
                                continue

                            return_thread, finished = _live_started(
                                port_info, platform, record_url, record_quality_zh,
                                record_name, anchor_name, record_proxy_address,
                            )
                            if return_thread:
                                return
                            if finished:
                                record_finished = True
                            count_time = time.time()
                except Exception as e:  # noqa: BLE001
                    _record_error(e)

                _sleep_until_next_check(anchor_name, record_finished, count_time)
                if record_finished:
                    record_finished = False

        except Exception as e:  # noqa: BLE001
            _record_error(e)
            time.sleep(2)
