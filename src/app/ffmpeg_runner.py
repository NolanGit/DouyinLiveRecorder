# -*- encoding: utf-8 -*-
"""ffmpeg subprocess driver and direct (httpx) FLV stream downloader."""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from pathlib import Path

import httpx

from src.utils import logger
from src import utils
from ffmpeg_install import check_ffmpeg

from . import state
from .file_ops import get_no_proxy_env, get_startup_info
from .naming import get_record_headers
from .post_process import converts_mp4, generate_subtitles


def run_script(command: str) -> None:
    """Execute a user-provided shell command after a recording session."""
    try:
        process = subprocess.Popen(
            command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=get_startup_info(state.os_type),
        )
        stdout, stderr = process.communicate()
        if stdout.decode('utf-8').strip():
            print(stdout.decode('utf-8'))
        if stderr.decode('utf-8').strip():
            print(stderr.decode('utf-8'))
    except PermissionError as e:
        logger.error(e)
        logger.error('脚本无执行权限!, 若是Linux环境, 请先执行:chmod +x your_script.sh 授予脚本可执行权限')
    except OSError as e:
        logger.error(e)
        logger.error('Please add `#!/bin/bash` at the beginning of your bash script file.')


def clear_record_info(record_name: str, record_url: str) -> None:
    """Mark a recording session as finished and remove it from runtime lists."""
    state.recording.discard(record_name)
    if record_url in state.url_comments and record_url in state.running_list:
        state.running_list.remove(record_url)
        state.monitoring -= 1
        state.color_obj.print_colored(
            f"[{record_name}]已经从录制列表中移除\n", state.color_obj.YELLOW,
        )


def direct_download_stream(source_url: str, save_path: str, record_name: str,
                           live_url: str, platform: str,
                           proxy_addr: str | None = None) -> bool:
    """Download a FLV stream straight to disk (used by FLV-only platforms)."""
    try:
        with open(save_path, 'wb') as f:
            client = httpx.Client(
                timeout=None,
                proxy=utils.handle_proxy_addr(proxy_addr),
                trust_env=False,
            )
            headers: dict[str, str] = {}
            header_params = get_record_headers(platform, live_url)
            if header_params:
                key, value = header_params.split(":", 1)
                headers[key] = value

            with client.stream('GET', source_url, headers=headers, follow_redirects=True) as response:
                if response.status_code != 200:
                    logger.error(f"请求直播流失败，状态码: {response.status_code}")
                    return False
                downloaded = 0
                chunk_size = 1024 * 16
                for chunk in response.iter_bytes(chunk_size):
                    if live_url in state.url_comments or state.exit_recording:
                        state.color_obj.print_colored(
                            f"[{record_name}]录制时已被注释或请求停止,下载中断",
                            state.color_obj.YELLOW,
                        )
                        clear_record_info(record_name, live_url)
                        return False
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                print()
                return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"FLV下载错误: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
        return False


def check_subprocess(record_name: str, record_url: str, ffmpeg_command: list,
                     save_type: str, script_command: str | None = None,
                     proxy_addr: str | None = None) -> bool:
    """Run ffmpeg and stream the recording until completion or comment-out."""
    save_file_path = ffmpeg_command[-1]
    process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        startupinfo=get_startup_info(state.os_type),
        env=get_no_proxy_env(),
    )

    subs_file_path = save_file_path.rsplit('.', maxsplit=1)[0]
    subs_thread_name = f'subs_{Path(subs_file_path).name}'
    if state.create_time_file and not state.split_video_by_time and '音频' not in save_type:
        state.create_var[subs_thread_name] = threading.Thread(
            target=generate_subtitles, args=(record_name, subs_file_path),
        )
        state.create_var[subs_thread_name].daemon = True
        state.create_var[subs_thread_name].start()

    while process.poll() is None:
        if record_url in state.url_comments or state.exit_recording:
            state.color_obj.print_colored(
                f"[{record_name}]录制时已被注释,本条线程将会退出", state.color_obj.YELLOW,
            )
            clear_record_info(record_name, record_url)
            if os.name == 'nt':
                if process.stdin:
                    process.stdin.write(b'q')
                    process.stdin.close()
            else:
                process.send_signal(signal.SIGINT)
            process.wait()
            return True
        # 性能优化：用 wait(timeout) 替代 sleep(1) 轮询
        # 进程退出时立即唤醒；2 秒检查一次注释/退出标记（响应延迟可接受）
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass

    return_code = process.returncode
    stop_time = time.strftime('%Y-%m-%d %H:%M:%S')
    if return_code == 0:
        if state.converts_to_mp4 and save_type == 'TS':
            if state.split_video_by_time:
                file_paths = utils.get_file_paths(os.path.dirname(save_file_path))
                prefix = os.path.basename(save_file_path).rsplit('_', maxsplit=1)[0]
                for path in file_paths:
                    if prefix in path:
                        threading.Thread(
                            target=converts_mp4, args=(path, state.delete_origin_file),
                        ).start()
            else:
                threading.Thread(
                    target=converts_mp4, args=(save_file_path, state.delete_origin_file),
                ).start()
        print(f"\n{record_name} {stop_time} 直播录制完成\n")

        if script_command:
            logger.debug("开始执行脚本命令!")
            if "python" in script_command:
                params = [
                    f'--record_name "{record_name}"',
                    f'--save_file_path "{save_file_path}"',
                    f'--save_type {save_type}',
                    f'--split_video_by_time {state.split_video_by_time}',
                    f'--converts_to_mp4 {state.converts_to_mp4}',
                ]
            else:
                params = [
                    f'"{record_name.split(" ", maxsplit=1)[-1]}"',
                    f'"{save_file_path}"',
                    save_type,
                    f'split_video_by_time:{state.split_video_by_time}',
                    f'converts_to_mp4:{state.converts_to_mp4}',
                ]
            script_command = script_command.strip() + ' ' + ' '.join(params)
            run_script(script_command)
            logger.debug("脚本命令执行结束!")
    else:
        state.color_obj.print_colored(
            f"\n{record_name} {stop_time} 直播录制出错,返回码: {return_code}\n",
            state.color_obj.RED,
        )

    state.recording.discard(record_name)
    return False


def check_ffmpeg_existence() -> bool:
    """Probe whether ffmpeg is reachable from PATH; install on first use."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], check=True, capture_output=True, text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(lines[0])
            print(lines[1])
    except subprocess.CalledProcessError as e:
        logger.error(e)
    except FileNotFoundError:
        pass
    finally:
        if check_ffmpeg():
            time.sleep(1)
            return True
    return False
