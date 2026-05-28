# -*- encoding: utf-8 -*-

import json
import re
import time

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_tiktok_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict | None:
    headers = {
        'referer': 'https://www.tiktok.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/141.0.0.0 Safari/537.36',
        'cookie': cookies or '1%7Cz7FKki38aKyy7i-BC9rEDwcrVvjcLcFEL6QIeqldoy4%7C1761302831%7C6c1461e9f1f980cbe0404c5190'
                             '5177d5d53bbd822e1bf66128887d942c9c3e2f'
    }

    for i in range(3):
        html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers, abroad=True, http2=False)
        time.sleep(1)
        if "We regret to inform you that we have discontinued operating TikTok" in html_str:
            msg = re.search('<p>\n\\s+(We regret to inform you that we have discontinu.*?)\\.\n\\s+</p>', html_str)
            raise ConnectionError(
                "Your proxy node's regional network is blocked from accessing TikTok; please switch to a node in "
                f"another region to access. {msg.group(1) if msg else ''}"
            )
        if 'UNEXPECTED_EOF_WHILE_READING' not in html_str:
            try:
                json_str = re.findall(
                    '<script id="SIGI_STATE" type="application/json">(.*?)</script>',
                    html_str, re.DOTALL)[0]
            except Exception:
                raise ConnectionError("Please check if your network can access the TikTok website normally")
            json_data = json.loads(json_str)
            return json_data
