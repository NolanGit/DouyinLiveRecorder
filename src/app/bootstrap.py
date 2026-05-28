# -*- encoding: utf-8 -*-
"""应用启动引导与主调度循环。

提供 :func:`run` 作为程序入口，由顶层 ``main.py`` 调用。
功能与重构前的单体脚本完全一致，仅将各职责委派给专用子模块。
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
from .time_window import TimeWindowConfig, is_within_window
from .url_loader import ensure_url_config_ready, parse_url_config


def _signal_handler(_signal, _frame):
    """捕获 SIGTERM 信号，确保进程能够优雅退出。"""
    sys.exit(0)


def _print_banner() -> None:
    """在终端打印程序启动横幅，包含版本号、项目地址和支持平台数量。"""
    print("-----------------------------------------------------")
    print("|                DouyinLiveRecorder                 |")
    print("-----------------------------------------------------")
    print(f"版本号: {state.version}")
    print("GitHub: https://github.com/ihmily/DouyinLiveRecorder")
    print(f'支持平台: {state.platforms}')
    print('.....................................................')


def _initialise() -> None:
    """进入主循环前的一次性初始化流程。

    依次完成以下工作：
    1. 创建运行时所需的目录结构
    2. 将 ffmpeg 路径注入系统 PATH
    3. 注册 SIGTERM 信号处理器
    4. 初始化语言/国际化配置并打印启动横幅
    5. 检查 ffmpeg 是否存在，不存在则退出
    6. 确保配置文件目录存在
    7. 启动后台线程定期备份 URL 配置文件
    8. 去重 URL 配置文件中的重复行
    9. 检测系统全局代理设置
    """
    state.ensure_runtime_dirs()
    # 将 ffmpeg 可执行文件路径添加到环境变量，确保子进程可调用
    os.environ['PATH'] = ffmpeg_path + os.pathsep + current_env_path
    signal.signal(signal.SIGTERM, _signal_handler)

    config_mod.init_language()
    _print_banner()
    if not check_ffmpeg_existence():
        logger.error("缺少ffmpeg无法进行录制，程序退出")
        sys.exit(1)

    os.makedirs(os.path.dirname(state.config_file), exist_ok=True)
    # 守护线程：定期备份 URL 配置文件，防止意外丢失
    threading.Thread(target=backup_file_loop, daemon=True).start()
    utils.remove_duplicate_lines(state.url_config_file)
    config_mod.detect_global_proxy()


def _check_disk_capacity() -> bool:
    """检查磁盘剩余空间是否满足最低要求。

    当剩余空间低于 ``state.disk_space_limit`` (GB) 时：
    - 标记 ``state.exit_recording = True``，通知录制线程停止
    - 若当前没有录制任务在运行，直接退出程序

    Returns:
        始终返回 True（仅在空间不足且无录制任务时直接 sys.exit）
    """
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


def _is_in_monitoring_window() -> bool:
    """检查当前时刻是否在监控时间窗口内。

    若功能未开启，始终返回 True（不限制）。
    窗口外时打印一次提示信息。
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
    if is_within_window(tw_config):
        return True
    logger.debug(
        f"当前时间不在监控窗口内({state.time_window_start}-{state.time_window_end})，"
        f"暂停新任务启动"
    )
    return False


def _spawn_recorders() -> None:
    """为 URL_config.ini 中新增的直播地址启动录制线程。

    遍历去重后的 URL 列表，对每个尚未在运行列表中的地址：
    1. 跳过位于 not_record_list 中的地址（用户标记不录制）
    2. 创建守护线程执行 start_record，传入 (url_tuple, 序号)
    3. 将线程引用保存到 state.create_var 以便后续管理
    4. 在相邻线程启动之间添加延迟，避免瞬间并发过高

    当监控时间窗口功能开启且当前时刻不在窗口内时，跳过新任务启动，
    但不影响已在运行的录制线程（它们会自行完成当前直播录制）。
    """
    if not state.text_no_repeat_url:
        return

    # 时间窗口检查：窗口外不启动新的监控任务
    if not _is_in_monitoring_window():
        return

    for url_tuple in state.text_no_repeat_url:
        state.monitoring = len(state.running_list)
        # 跳过用户标记为不录制的地址
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
            # 启动间隔延迟，避免同一时刻大量并发请求
            time.sleep(state.local_delay_default)
    # 清空待处理列表，标记首次启动已完成
    state.url_tuples_list = []
    state.first_start = False


def run() -> None:
    """程序主入口，由顶层 ``main.py`` 调用。

    执行流程：
    1. 调用 _initialise() 完成一次性初始化
    2. 进入无限循环，每轮迭代依次：
       a. 确保 URL 配置文件就绪
       b. 加载/刷新 INI 配置（支持运行时修改配置热加载）
       c. 检查磁盘空间
       d. 解析 URL 配置文件，提取直播地址
       e. 为新地址启动录制线程
    3. 首轮循环结束后启动状态显示和并发调节的守护线程
    4. 每轮循环间隔 3 秒，实现对配置变更的周期性轮询
    """
    _initialise()

    while True:
        try:
            ensure_url_config_ready()       # 确保 URL_config.ini 存在
            config_mod.load()               # 加载/刷新配置项到 state
            _check_disk_capacity()          # 磁盘空间检查
            parse_url_config()              # 解析直播地址列表
            _spawn_recorders()              # 启动新增地址的录制线程
        except Exception as err:  # noqa: BLE001
            logger.error(
                f"错误信息: {err} 发生错误的行数: {err.__traceback__.tb_lineno}",
            )

        # 首次运行时启动监控线程：状态面板 + 并发数自动调节
        if state.first_run:
            threading.Thread(target=display_info, daemon=True).start()
            threading.Thread(target=adjust_max_request, daemon=True).start()
            state.first_run = False

        # 轮询间隔 3 秒，周期性检测配置变更和新增地址
        time.sleep(3)
