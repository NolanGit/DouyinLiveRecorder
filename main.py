# -*- encoding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily/DouyinLiveRecorder
Date: 2023-07-17 23:52:05
Update: 2025-10-23 19:48:05
Copyright (c) 2023-2025 by Hmily, All Rights Reserved.
Function: Record live stream video.

This entry point keeps backwards compatibility with ``python main.py``.
The implementation has been refactored into the :mod:`src.app` package; see
``ARCHITECTURE.md`` for the module layout and dependency graph.
"""

from src.app.bootstrap import run


if __name__ == "__main__":
    run()
