# -*- encoding: utf-8 -*-

import json
import re
import urllib.parse

import execjs

from .base import OptionalStr, async_req, trace_error_decorator, JS_SCRIPT_PATH, IOS_UA


# 模块加载时一次性读取并编译 JS，避免每次直播探测都 open/read/compile
_LIVEME_JS = execjs.compile(open(f'{JS_SCRIPT_PATH}/liveme.js').read())


@trace_error_decorator
async def get_liveme_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.liveme.com',
        'referer': 'https://www.liveme.com',
        'user-agent': IOS_UA,
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'index.html' not in url:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers, abroad=True)
        match_url = re.search('<meta property="og:url" content="(.*?)">', html_str)
        if match_url:
            url = match_url.group(1)

    room_id = url.split("/index.html")[0].rsplit('/', maxsplit=1)[-1]
    sign_data = _LIVEME_JS.call('sign', room_id, f'{JS_SCRIPT_PATH}/crypto-js.min.js')
    lm_s_sign = sign_data.pop("lm_s_sign")
    tongdun_black_box = sign_data.pop("tongdun_black_box")
    platform = sign_data.pop("os")
    headers['lm-s-sign'] = lm_s_sign

    params = {
        'alias': 'liveme',
        'tongdun_black_box': tongdun_black_box,
        'os': platform,
    }

    api = f'https://live.liveme.com/live/queryinfosimple?{urllib.parse.urlencode(params)}'
    json_str = await async_req(api, data=sign_data, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    stream_data = json_data['data']['video_info']
    anchor_name = stream_data['uname']
    live_status = stream_data['status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == "0":
        m3u8_url = stream_data['hlsvideosource']
        flv_url = stream_data['videosource']
        result |= {
            'is_live': True,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': m3u8_url or flv_url
        }
    return result
