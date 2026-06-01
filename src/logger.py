# -*- coding: utf-8 -*-

import os
import sys
from loguru import logger

logger.remove()

custom_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> - <level>{message}</level>"

logger.add(
    sink=sys.stderr,
    format=custom_format,
    level="DEBUG",
    colorize=True,
    enqueue=True
)

script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]

logger.add(
    f"{script_path}/logs/streamget.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    filter=lambda i: i["level"].name != "INFO",
    serialize=False,
    enqueue=True,
    # 旋转参数放大：原 300KB / retention=1 在错误密集场景下分钟级触发
    # rename + retention 删除，磁盘 IO 频繁。提到 5MB / retention=3 后
    # 文件 IO 量降低 1-2 个数量级，仍能覆盖最近的调试日志。
    retention=3,
    rotation="5 MB",
    encoding='utf-8'
)

logger.add(
    f"{script_path}/logs/PlayURL.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
    filter=lambda i: i["level"].name == "INFO",
    serialize=False,
    enqueue=True,
    retention=3,
    rotation="5 MB",
    encoding='utf-8'
)
