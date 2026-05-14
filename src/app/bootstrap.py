# -*- encoding: utf-8 -*-
"""Application bootstrap & main scheduling loop.

Provides :func:`run` which is invoked by the legacy ``main.py`` entry point.
Behaviour is identical to the original monolithic script - the only change is
that responsibility is now delegated to specialised modules.
"""
from __future__ import annotations

import os
import signal
import sys
import threading
import time

from ffmpeg_install import current_env_path, ffmpeg_path
from src import utils
from src.utils import logger

from . import config as config_mod
from . import state
from .ffmpeg_runner import check_ffmpeg_existence
from .file_ops import backup_file_loop
from .monitor import adjust_max_request, display_info
from .recorder import start_record
from .url_loader import ensure_url_config_ready, parse_url_config


def _signal_handler(_signal, _frame):
    sys.exit(0)


def _print_banner() -> None:
    print("-----------------------------------------------------")
    print("|                DouyinLiveRecorder                 |")
    print("-----------------------------------------------------")
    print(f"版本号: {state.version}")
    print("GitHub: https://github.com/ihmily/DouyinLiveRecorder")
    print(f'支持平台: {state.platforms}')
    print('.....................................................')


def _initialise() -> None:
    """One-time process setup performed before entering the main loop."""
    state.ensure_runtime_dirs()
    os.environ['PATH'] = ffmpeg_path + os.pathsep + current_env_path
    signal.signal(signal.SIGTERM, _signal_handler)

    config_mod.init_language()
    _print_banner()
    if not check_ffmpeg_existence():
        logger.error("缺少ffmpeg无法进行录制，程序退出")
        sys.exit(1)

    os.makedirs(os.path.dirname(state.config_file), exist_ok=True)
    threading.Thread(target=backup_file_loop, daemon=True).start()
    utils.remove_duplicate_lines(state.url_config_file)
    config_mod.detect_global_proxy()


def _check_disk_capacity() -> bool:
    check_path = state.video_save_path or state.default_path
    if utils.check_disk_capacity(check_path, show=state.first_run) < state.disk_space_limit:
        state.exit_recording = True
        if not state.recording:
            logger.warning(
                f"Disk space remaining is below {state.disk_space_limit} GB. "
                f"Exiting program due to the disk space limit being reached.",
            )
            sys.exit(-1)
    return True


def _spawn_recorders() -> None:
    """Spawn one daemon thread per new URL detected in URL_config.ini."""
    if not state.text_no_repeat_url:
        return
    for url_tuple in state.text_no_repeat_url:
        state.monitoring = len(state.running_list)
        if url_tuple[1] in state.not_record_list:
            continue
        if url_tuple[1] not in state.running_list:
            print(f"\r{'新增' if not state.first_start else '传入'}地址: {url_tuple[1]}")
            state.monitoring += 1
            args = [url_tuple, state.monitoring]
            t = threading.Thread(target=start_record, args=args, daemon=True)
            state.create_var[f'thread_{state.monitoring}'] = t
            t.start()
            state.running_list.append(url_tuple[1])
            time.sleep(state.local_delay_default)
    state.url_tuples_list = []
    state.first_start = False


def run() -> None:
    """Module entry point used by the top-level ``main.py``."""
    _initialise()

    while True:
        try:
            ensure_url_config_ready()
            config_mod.load()
            _check_disk_capacity()
            parse_url_config()
            _spawn_recorders()
        except Exception as err:  # noqa: BLE001
            logger.error(
                f"错误信息: {err} 发生错误的行数: {err.__traceback__.tb_lineno}",
            )

        if state.first_run:
            threading.Thread(target=display_info, daemon=True).start()
            threading.Thread(target=adjust_max_request, daemon=True).start()
            state.first_run = False

        time.sleep(3)
