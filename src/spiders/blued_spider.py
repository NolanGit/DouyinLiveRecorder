# -*- encoding: utf-8 -*-

import json
import re
import urllib.parse

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_blued_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    json_str = re.search('decodeURIComponent\\(\"(.*?)\"\\)\\),window\\.Promise', html_str, re.DOTALL).group(1)
    json_str = urllib.parse.unquote(json_str)
    json_data = json.loads(json_str)
    anchor_name = json_data['userInfo']['name']
    live_status = json_data['userInfo']['onLive']
    result = {"anchor_name": anchor_name, "is_live": False}

    if live_status:
        m3u8_url = json_data['liveInfo']['liveUrl']
        result |= {"is_live": True, "m3u8_url": m3u8_url, 'record_url': m3u8_url}
    return result
