# -*- encoding: utf-8 -*-
"""Per-format ffmpeg invocation helpers (FLV / MKV / MP4 / TS)."""
from __future__ import annotations

import os
import subprocess
import threading
import time

from src.utils import logger
from src import utils

from . import state
from .ffmpeg_runner import check_subprocess
from .post_process import converts_mp4, segment_video


def _do_check(record_name, record_url, ffmpeg_command,
              record_save_type, record_proxy_address):
    return check_subprocess(
        record_name, record_url, ffmpeg_command, record_save_type,
        state.custom_script, record_proxy_address,
    )


def record_flv(ffmpeg_command, full_path, anchor_name, title_in_name, now,
               record_save_type, record_name, record_url, record_proxy_address):
    filename = anchor_name + f'_{title_in_name}' + now + ".flv"
    save_file_path = full_path + '/' + filename
    print(f'\r{anchor_name} 准备开始录制视频: {full_path}/{filename}')
    if state.split_video_by_time:
        now2 = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now2}_%03d.flv"
        command = [
            "-map", "0", "-c:v", "copy", "-c:a", "copy", "-bsf:a", "aac_adtstoasc",
            "-f", "segment", "-segment_time", state.split_time,
            "-segment_format", "flv", "-reset_timestamps", "1", save_file_path,
        ]
    else:
        command = [
            "-map", "0", "-c:v", "copy", "-c:a", "copy",
            "-bsf:a", "aac_adtstoasc", "-f", "flv", save_file_path,
        ]
    ffmpeg_command.extend(command)
    comment_end = _do_check(
        record_name, record_url, ffmpeg_command, record_save_type, record_proxy_address,
    )
    try:
        if state.converts_to_mp4:
            seg_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.mp4"
            if state.split_video_by_time:
                segment_video(
                    save_file_path, seg_file_path,
                    segment_format='mp4', segment_time=state.split_time,
                    is_original_delete=state.delete_origin_file,
                )
            else:
                threading.Thread(
                    target=converts_mp4, args=(save_file_path, state.delete_origin_file),
                ).start()
        elif state.split_video_by_time:
            seg_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.flv"
            segment_video(
                save_file_path, seg_file_path,
                segment_format='flv', segment_time=state.split_time,
                is_original_delete=state.delete_origin_file,
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"转码失败: {e} ")
    return comment_end


def record_mkv(ffmpeg_command, full_path, anchor_name, title_in_name, now,
               record_save_type, record_name, record_url, record_proxy_address):
    filename = anchor_name + f'_{title_in_name}' + now + ".mkv"
    save_file_path = full_path + '/' + filename
    print(f'\r{anchor_name} 准备开始录制视频: {full_path}/{filename}')
    if state.split_video_by_time:
        now2 = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now2}_%03d.mkv"
        command = [
            "-flags", "global_header", "-c:v", "copy", "-c:a", "aac",
            "-map", "0", "-f", "segment", "-segment_time", state.split_time,
            "-segment_format", "matroska", "-reset_timestamps", "1", save_file_path,
        ]
    else:
        command = [
            "-flags", "global_header", "-map", "0", "-c:v", "copy",
            "-c:a", "copy", "-f", "matroska", save_file_path,
        ]
    ffmpeg_command.extend(command)
    return _do_check(
        record_name, record_url, ffmpeg_command, record_save_type, record_proxy_address,
    )


def record_mp4(ffmpeg_command, full_path, anchor_name, title_in_name, now,
               record_save_type, record_name, record_url, record_proxy_address):
    filename = anchor_name + f'_{title_in_name}' + now + ".mp4"
    save_file_path = full_path + '/' + filename
    print(f'\r{anchor_name} 准备开始录制视频: {full_path}/{filename}')
    if state.split_video_by_time:
        now2 = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now2}_%03d.mp4"
        command = [
            "-c:v", "copy", "-c:a", "aac", "-map", "0",
            "-f", "segment", "-segment_time", state.split_time,
            "-segment_format", "mp4", "-reset_timestamps", "1",
            "-movflags", "+frag_keyframe+empty_moov", save_file_path,
        ]
    else:
        command = [
            "-map", "0", "-c:v", "copy", "-c:a", "copy",
            "-f", "mp4", save_file_path,
        ]
    ffmpeg_command.extend(command)
    return _do_check(
        record_name, record_url, ffmpeg_command, record_save_type, record_proxy_address,
    )


def record_ts(ffmpeg_command, full_path, anchor_name, title_in_name, now,
              record_save_type, record_name, record_url, record_proxy_address):
    if state.split_video_by_time:
        now2 = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        filename = anchor_name + f'_{title_in_name}' + now2 + ".ts"
        save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now2}_%03d.ts"
        print(f'\r{anchor_name} 准备开始录制视频: {full_path}/{filename}')
        command = [
            "-c:v", "copy", "-c:a", "copy", "-map", "0",
            "-f", "segment", "-segment_time", state.split_time,
            "-segment_format", 'mpegts', "-reset_timestamps", "1", save_file_path,
        ]
        ffmpeg_command.extend(command)
        comment_end = _do_check(
            record_name, record_url, ffmpeg_command, record_save_type, record_proxy_address,
        )
        if comment_end and state.converts_to_mp4:
            file_paths = utils.get_file_paths(os.path.dirname(save_file_path))
            prefix = os.path.basename(save_file_path).rsplit('_', maxsplit=1)[0]
            for path in file_paths:
                if prefix in path:
                    try:
                        threading.Thread(
                            target=converts_mp4, args=(path, state.delete_origin_file),
                        ).start()
                    except subprocess.CalledProcessError as e:
                        logger.error(f"转码失败: {e} ")
        return comment_end

    filename = anchor_name + f'_{title_in_name}' + now + ".ts"
    save_file_path = full_path + '/' + filename
    print(f'\r{anchor_name} 准备开始录制视频: {full_path}/{filename}')
    command = [
        "-c:v", "copy", "-c:a", "copy", "-map", "0", "-f", "mpegts", save_file_path,
    ]
    ffmpeg_command.extend(command)
    comment_end = _do_check(
        record_name, record_url, ffmpeg_command, record_save_type, record_proxy_address,
    )
    if comment_end:
        threading.Thread(
            target=converts_mp4, args=(save_file_path, state.delete_origin_file),
        ).start()
    return comment_end


FORMAT_HANDLERS = {
    "FLV": record_flv,
    "MKV": record_mkv,
    "MP4": record_mp4,
    "TS": record_ts,
}
