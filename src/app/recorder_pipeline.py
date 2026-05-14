# -*- encoding: utf-8 -*-
"""ffmpeg base command construction & high level recording dispatch.

Per-format ffmpeg invocation lives in :mod:`recorder_format`. This module
builds the base ffmpeg argv, computes save paths, runs audio-only and direct
FLV download flows, and dispatches non-audio recordings by save format.
"""
from __future__ import annotations

import datetime
import os
import threading
import time
from pathlib import Path

from src.utils import logger

from . import state
from .ffmpeg_runner import (
    check_subprocess, direct_download_stream,
)
from .naming import clean_name, get_record_headers
from .post_process import generate_subtitles
from .recorder_format import FORMAT_HANDLERS, record_ts


_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 ("
    "KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile "
    "Safari/537.36"
)


def build_ffmpeg_base(real_url: str, record_url: str, platform: str,
                      record_proxy_address: str | None) -> list[str]:
    """Construct the common ffmpeg command prefix for a recording session."""
    rw_timeout = "15000000"
    analyzeduration = "20000000"
    probesize = "10000000"
    bufsize = "8000k"
    max_muxing_queue_size = "1024"

    for pt_host in state.OVERSEAS_PLATFORM_HOST:
        if pt_host in record_url:
            rw_timeout = "50000000"
            analyzeduration = "40000000"
            probesize = "20000000"
            bufsize = "15000k"
            max_muxing_queue_size = "2048"
            break

    cmd = [
        'ffmpeg', "-y",
        "-v", "verbose",
        "-rw_timeout", rw_timeout,
        "-loglevel", "error",
        "-hide_banner",
        "-user_agent", _USER_AGENT,
        "-protocol_whitelist", "rtmp,crypto,file,http,https,tcp,tls,udp,rtp,httpproxy",
        "-thread_queue_size", "1024",
        "-analyzeduration", analyzeduration,
        "-probesize", probesize,
        "-fflags", "+discardcorrupt",
        "-re", "-i", real_url,
        "-bufsize", bufsize,
        "-sn", "-dn",
        "-reconnect_delay_max", "60",
        "-reconnect_streamed", "-reconnect_at_eof",
        "-max_muxing_queue_size", max_muxing_queue_size,
        "-correct_ts_overflow", "1",
        "-avoid_negative_ts", "1",
    ]

    headers = get_record_headers(platform, record_url)
    if headers:
        cmd.insert(11, "-headers")
        cmd.insert(12, headers)

    if record_proxy_address:
        cmd.insert(1, "-http_proxy")
        cmd.insert(2, record_proxy_address)
    return cmd


def build_save_path(platform: str, anchor_name: str, port_info: dict, now: str) -> tuple[str, str]:
    """Return ``(full_path, title_in_name)`` for the current recording."""
    full_path = f'{state.default_path}/{platform}'
    live_title = port_info.get('title')
    title_in_name = ''
    if live_title:
        live_title = clean_name(live_title)
        title_in_name = live_title + '_' if state.filename_by_title else ''

    try:
        if len(state.video_save_path) > 0:
            if not state.video_save_path.endswith(('/', '\\')):
                full_path = f'{state.video_save_path}/{platform}'
            else:
                full_path = f'{state.video_save_path}{platform}'

        full_path = full_path.replace("\\", '/')
        if state.folder_by_author:
            full_path = f'{full_path}/{anchor_name}'
        if state.folder_by_time:
            full_path = f'{full_path}/{now[:10]}'
        if state.folder_by_title and port_info.get('title'):
            if state.folder_by_time:
                full_path = f'{full_path}/{live_title}_{anchor_name}'
            else:
                full_path = f'{full_path}/{now[:10]}_{live_title}'
        if not os.path.exists(full_path):
            os.makedirs(full_path)
    except Exception as e:  # noqa: BLE001
        logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")

    return full_path, title_in_name


def record_audio(ffmpeg_command: list, full_path: str, anchor_name: str,
                 title_in_name: str, record_save_type: str, record_name: str,
                 record_url: str, record_proxy_address: str | None) -> bool:
    """Append audio-only encoding flags and run ffmpeg."""
    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    extension = "mp3" if "m4a" not in record_save_type.lower() else "m4a"
    name_format = "_%03d" if state.split_video_by_time else ""
    save_file_path = (
        f"{full_path}/{anchor_name}_{title_in_name}{now}{name_format}.{extension}"
    )

    if state.split_video_by_time:
        print(f'\r{anchor_name} 准备开始录制音频: {save_file_path}')
        if "MP3" in record_save_type:
            command = [
                "-map", "0:a", "-c:a", "libmp3lame", "-ab", "320k",
                "-f", "segment", "-segment_time", state.split_time,
                "-reset_timestamps", "1", save_file_path,
            ]
        else:
            command = [
                "-map", "0:a", "-c:a", "aac", "-bsf:a", "aac_adtstoasc",
                "-ab", "320k", "-f", "segment",
                "-segment_time", state.split_time,
                "-segment_format", 'mpegts',
                "-reset_timestamps", "1", save_file_path,
            ]
    else:
        if "MP3" in record_save_type:
            command = ["-map", "0:a", "-c:a", "libmp3lame", "-ab", "320k", save_file_path]
        else:
            command = [
                "-map", "0:a", "-c:a", "aac", "-bsf:a", "aac_adtstoasc",
                "-ab", "320k", "-movflags", "+faststart", save_file_path,
            ]

    ffmpeg_command.extend(command)
    return check_subprocess(
        record_name, record_url, ffmpeg_command, record_save_type,
        state.custom_script, record_proxy_address,
    )


def record_flv_direct(port_info: dict, full_path: str, anchor_name: str,
                      title_in_name: str, now: str, record_quality_zh: str,
                      record_name: str, record_url: str, platform: str,
                      record_proxy_address: str | None) -> bool:
    """FLV-only platforms use a direct httpx downloader rather than ffmpeg."""
    filename = anchor_name + f'_{title_in_name}' + now + '.flv'
    save_file_path = f'{full_path}/{filename}'
    print(f"\r{anchor_name} 准备开始录制视频: {full_path}/{filename}")

    subs_file_path = save_file_path.rsplit('.', maxsplit=1)[0]
    subs_thread_name = f'subs_{Path(subs_file_path).name}'
    if state.create_time_file:
        state.create_var[subs_thread_name] = threading.Thread(
            target=generate_subtitles, args=(record_name, subs_file_path),
        )
        state.create_var[subs_thread_name].daemon = True
        state.create_var[subs_thread_name].start()

    flv_url = port_info.get('flv_url')
    if not flv_url:
        logger.debug("未找到FLV直播流，跳过录制")
        return False

    state.recording.add(record_name)
    state.recording_time_list[record_name] = [datetime.datetime.now(), record_quality_zh]
    download_success = direct_download_stream(
        flv_url, save_file_path, record_name, record_url, platform, record_proxy_address,
    )
    if download_success:
        print(f"\n{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制完成\n")
    state.recording.discard(record_name)
    return download_success


def record_with_format(ffmpeg_command: list, record_save_type: str,
                       full_path: str, anchor_name: str, title_in_name: str,
                       now: str, record_name: str, record_url: str,
                       record_proxy_address: str | None) -> bool:
    """Dispatch on save format and run ffmpeg + post-processing."""
    handler = FORMAT_HANDLERS.get(record_save_type, record_ts)
    return handler(
        ffmpeg_command, full_path, anchor_name, title_in_name, now,
        record_save_type, record_name, record_url, record_proxy_address,
    )
