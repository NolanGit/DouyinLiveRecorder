# -*- encoding: utf-8 -*-
"""Filesystem helpers used to mutate config / URL files in-place.

These helpers are kept thin so they can be unit-tested in isolation. Any
state-shared behaviour (locks, encoding) reads from :mod:`src.app.state`.
"""
from __future__ import annotations

import datetime
import os
import shutil
import subprocess
import time

from src.utils import logger
from src import utils

from . import state


def get_startup_info(system_type: str):
    """Return Windows ``STARTUPINFO`` to hide subprocess windows or ``None``."""
    if system_type == 'nt':
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startup_info
    return None


def get_no_proxy_env() -> dict:
    """Return a copy of os.environ with all proxy-related entries removed."""
    env = os.environ.copy()
    for key in (
        'http_proxy', 'https_proxy', 'ftp_proxy', 'all_proxy', 'no_proxy',
        'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'ALL_PROXY', 'NO_PROXY',
    ):
        env.pop(key, None)
    return env


def update_file(file_path: str, old_str: str, new_str: str, start_str: str | None = None) -> str | None:
    """Replace ``old_str`` with ``new_str`` in ``file_path`` (in-place, dedup lines)."""
    if old_str == new_str and start_str is None:
        return old_str
    with state.file_update_lock:
        file_data: list[str] = []
        with open(file_path, "r", encoding=state.text_encoding) as f:
            try:
                for text_line in f:
                    if old_str in text_line:
                        text_line = text_line.replace(old_str, new_str)
                        if start_str:
                            text_line = f'{start_str}{text_line}'
                    if text_line not in file_data:
                        file_data.append(text_line)
            except RuntimeError as e:
                logger.error(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
                if state.ini_URL_content:
                    with open(file_path, "w", encoding=state.text_encoding) as f2:
                        f2.write(state.ini_URL_content)
                    return old_str
        if file_data:
            with open(file_path, "w", encoding=state.text_encoding) as f:
                f.write(''.join(file_data))
        return new_str


def delete_line(file_path: str, del_line: str, delete_all: bool = False) -> None:
    """Delete first (or all) occurrences of ``del_line`` in ``file_path``."""
    with state.file_update_lock:
        with open(file_path, 'r+', encoding=state.text_encoding) as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            skip_line = False
            for txt_line in lines:
                if del_line in txt_line:
                    if delete_all or not skip_line:
                        skip_line = True
                        continue
                else:
                    skip_line = False
                f.write(txt_line)


def backup_file(file_path: str, backup_dir_path: str, limit_counts: int = 6) -> None:
    """Create a timestamped backup, keeping at most ``limit_counts`` copies."""
    try:
        if not os.path.exists(backup_dir_path):
            os.makedirs(backup_dir_path)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file_name = os.path.basename(file_path) + '_' + timestamp
        backup_file_path = os.path.join(backup_dir_path, backup_file_name).replace("\\", "/")
        shutil.copy2(file_path, backup_file_path)

        files = os.listdir(backup_dir_path)
        _files = [f for f in files if f.startswith(os.path.basename(file_path))]
        _files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir_path, x)))

        while len(_files) > limit_counts:
            oldest_file = _files[0]
            os.remove(os.path.join(backup_dir_path, oldest_file))
            _files = _files[1:]
    except Exception as e:
        logger.error(f'\r备份配置文件 {file_path} 失败：{str(e)}')


def backup_file_loop() -> None:
    """Daemon thread loop that backs up config files when they change."""
    config_md5 = ''
    url_config_md5 = ''
    while True:
        try:
            if os.path.exists(state.config_file):
                new_config_md5 = utils.check_md5(state.config_file)
                if new_config_md5 != config_md5:
                    backup_file(state.config_file, state.backup_dir)
                    config_md5 = new_config_md5

            if os.path.exists(state.url_config_file):
                new_url_config_md5 = utils.check_md5(state.url_config_file)
                if new_url_config_md5 != url_config_md5:
                    backup_file(state.url_config_file, state.backup_dir)
                    url_config_md5 = new_url_config_md5
            time.sleep(600)
        except Exception as e:
            logger.error(f"备份配置文件失败, 错误信息: {e}")
