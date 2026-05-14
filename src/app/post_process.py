# -*- encoding: utf-8 -*-
"""ffmpeg based post-processing helpers (segmenting / mp4 / m4a / subtitles)."""
from __future__ import annotations

import datetime
import os
import subprocess
import time

from src.utils import logger

from . import state
from .file_ops import get_startup_info


def segment_video(converts_file_path: str, segment_save_file_path: str,
                  segment_format: str, segment_time: str,
                  is_original_delete: bool = True) -> None:
    """Split an existing media file into time-bounded segments via ffmpeg."""
    try:
        if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
            ffmpeg_command = [
                "ffmpeg", "-i", converts_file_path,
                "-c:v", "copy", "-c:a", "copy", "-map", "0",
                "-f", "segment",
                "-segment_time", segment_time,
                "-segment_format", segment_format,
                "-reset_timestamps", "1",
                "-movflags", "+frag_keyframe+empty_moov",
                segment_save_file_path,
            ]
            subprocess.check_output(
                ffmpeg_command, stderr=subprocess.STDOUT,
                startupinfo=get_startup_info(state.os_type),
            )
            if is_original_delete:
                time.sleep(1)
                if os.path.exists(converts_file_path):
                    os.remove(converts_file_path)
    except subprocess.CalledProcessError as e:
        logger.error(f'Error occurred during conversion: {e}')
    except Exception as e:  # noqa: BLE001
        logger.error(f'An unknown error occurred: {e}')


def converts_mp4(converts_file_path: str, is_original_delete: bool = True) -> None:
    """Convert a media file to MP4, optionally re-encoding to H.264."""
    try:
        if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
            if state.converts_to_h264:
                state.color_obj.print_colored(
                    "正在转码为MP4格式并重新编码为h264\n", state.color_obj.YELLOW,
                )
                ffmpeg_command = [
                    "ffmpeg", "-i", converts_file_path,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-vf", "format=yuv420p", "-c:a", "copy",
                    "-f", "mp4", converts_file_path.rsplit('.', maxsplit=1)[0] + ".mp4",
                ]
            else:
                state.color_obj.print_colored("正在转码为MP4格式\n", state.color_obj.YELLOW)
                ffmpeg_command = [
                    "ffmpeg", "-i", converts_file_path,
                    "-c:v", "copy", "-c:a", "copy",
                    "-f", "mp4", converts_file_path.rsplit('.', maxsplit=1)[0] + ".mp4",
                ]
            subprocess.check_output(
                ffmpeg_command, stderr=subprocess.STDOUT,
                startupinfo=get_startup_info(state.os_type),
            )
            if is_original_delete:
                time.sleep(1)
                if os.path.exists(converts_file_path):
                    os.remove(converts_file_path)
    except subprocess.CalledProcessError as e:
        logger.error(f'Error occurred during conversion: {e}')
    except Exception as e:  # noqa: BLE001
        logger.error(f'An unknown error occurred: {e}')


def converts_m4a(converts_file_path: str, is_original_delete: bool = True) -> None:
    """Convert a media file to M4A audio."""
    try:
        if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
            subprocess.check_output(
                [
                    "ffmpeg", "-i", converts_file_path,
                    "-n", "-vn",
                    "-c:a", "aac", "-bsf:a", "aac_adtstoasc", "-ab", "320k",
                    converts_file_path.rsplit('.', maxsplit=1)[0] + ".m4a",
                ],
                stderr=subprocess.STDOUT,
                startupinfo=get_startup_info(state.os_type),
            )
            if is_original_delete:
                time.sleep(1)
                if os.path.exists(converts_file_path):
                    os.remove(converts_file_path)
    except subprocess.CalledProcessError as e:
        logger.error(f'Error occurred during conversion: {e}')
    except Exception as e:  # noqa: BLE001
        logger.error(f'An unknown error occurred: {e}')


def generate_subtitles(record_name: str, ass_filename: str, sub_format: str = 'srt') -> None:
    """Continuously append SRT entries while ``record_name`` is being recorded."""
    index_time = 0
    today = datetime.datetime.now()
    re_datatime = today.strftime('%Y-%m-%d %H:%M:%S')

    def transform(seconds: int) -> str:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    while True:
        index_time += 1
        txt = (
            f"{index_time}\n"
            f"{transform(index_time)},000 --> {transform(index_time + 1)},000\n"
            f"{re_datatime}\n\n"
        )
        with open(f"{ass_filename}.{sub_format.lower()}", 'a', encoding=state.text_encoding) as f:
            f.write(txt)
        if record_name not in state.recording:
            return
        time.sleep(1)
        today = datetime.datetime.now()
        re_datatime = today.strftime('%Y-%m-%d %H:%M:%S')
