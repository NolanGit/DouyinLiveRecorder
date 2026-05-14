# -*- encoding: utf-8 -*-
"""Pure helper functions for naming, quality codes, headers, source picking.

These functions have **no side effects** and read at most a couple of
configuration values from :mod:`src.app.state`, making them trivial to unit
test. They were lifted verbatim out of the original ``main.py``.
"""
from __future__ import annotations

import re

from src.utils import logger
from src import utils

from . import state


_QUALITY_MAPPING = {
    "原画": "OD",
    "蓝光": "BD",
    "超清": "UHD",
    "高清": "HD",
    "标清": "SD",
    "流畅": "LD",
}


def get_quality_code(qn: str) -> str | None:
    """Translate a Chinese quality label into the spider/stream module code."""
    return _QUALITY_MAPPING.get(qn)


def clean_name(input_text: str) -> str:
    """Sanitise a string so it is safe to use inside a filesystem path."""
    cleaned_name = re.sub(state.rstr, "_", input_text.strip()).strip('_')
    cleaned_name = cleaned_name.replace("（", "(").replace("）", ")")
    if state.clean_emoji:
        cleaned_name = utils.remove_emojis(cleaned_name, '_').strip('_')
    return cleaned_name or '空白昵称'


_RECORD_HEADERS = {
    'PandaTV': 'origin:https://www.pandalive.co.kr',
    'WinkTV': 'origin:https://www.winktv.co.kr',
    'PopkonTV': 'origin:https://www.popkontv.com',
    'FlexTV': 'origin:https://www.flextv.co.kr',
    '千度热播': 'referer:https://qiandurebo.com',
    '17Live': 'referer:https://17.live/en/live/6302408',
    '浪Live': 'referer:https://www.lang.live',
    'Blued直播': 'referer:https://app.blued.cn',
}


def get_record_headers(platform: str, live_url: str) -> str | None:
    """Return per-platform request header (``key:value``) used by ffmpeg."""
    live_domain = '/'.join(live_url.split('/')[0:3])
    headers = dict(_RECORD_HEADERS)
    headers['shopee'] = f'origin:{live_domain}'
    return headers.get(platform)


def is_flv_preferred_platform(link: str) -> bool:
    """Whether FLV stream is preferred for the given live URL."""
    return any(i in link for i in ("douyin", "tiktok"))


def select_source_url(link: str, stream_info: dict) -> str | None:
    """Choose between the available FLV / HLS sources based on platform & codec."""
    if is_flv_preferred_platform(link):
        codec = utils.get_query_params(stream_info.get('flv_url'), "codec")
        if codec and codec[0] == 'h265':
            logger.warning("FLV is not supported for h265 codec, use HLS source instead")
        else:
            return stream_info.get('flv_url')
    return stream_info.get('record_url')


def contains_url(string: str) -> bool:
    """Light-weight URL detector used by URL_config.ini parsing."""
    pattern = r"(https?://)?(www\.)?[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(:\d+)?(/.*)?"
    return re.search(pattern, string) is not None
