# -*- encoding: utf-8 -*-
"""
DouyinLiveRecorder application package.

Refactored from the original monolithic ``main.py``. The package is split
into single-responsibility modules:

    state                   -- shared mutable runtime state and constants
    config                  -- INI file loading and configuration assignment
    file_ops                -- low level URL/config file mutation helpers
    url_loader              -- URL_config.ini parsing & validation
    naming                  -- pure helpers for filename / quality / source select
    proxy_resolver          -- per-stage proxy decision
    notifier                -- multi-channel push-message dispatcher
    post_process            -- ffmpeg based transcoding / segmenting / subtitles
    ffmpeg_runner           -- ffmpeg subprocess driver and direct downloader
    monitor                 -- status display & dynamic thread adjustment
    platform_handlers_cn    -- domestic platform handler functions
    platform_handlers_os    -- overseas platform handler functions
    platform_registry       -- ``URL substring -> handler`` lookup table
    platform_dispatch       -- thin facade exposing :func:`dispatch`
    recorder_format         -- per-format ffmpeg command generators
    recorder_pipeline       -- ffmpeg base / save path / audio / FLV pipelines
    recorder                -- per-URL recording loop (``start_record``)
    bootstrap               -- top level :func:`run` entry & main scheduling loop
"""

__all__ = [
    "state",
    "config",
    "file_ops",
    "url_loader",
    "naming",
    "proxy_resolver",
    "notifier",
    "post_process",
    "ffmpeg_runner",
    "monitor",
    "platform_handlers_cn",
    "platform_handlers_os",
    "platform_registry",
    "platform_dispatch",
    "recorder_format",
    "recorder_pipeline",
    "recorder",
    "bootstrap",
]
