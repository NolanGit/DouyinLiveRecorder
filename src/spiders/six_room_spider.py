# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_6room_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://ios.6.cn/?ver=8.0.3&build=4',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    html_str = await async_req(f'https://v.6.cn/{room_id}', proxy_addr=proxy_addr, headers=headers)
    room_id = re.search('rid: \'(.*?)\',\n\\s+roomid', html_str).group(1)
    data = {
        'av': '3.1',
        'encpass': '',
        'logiuid': '',
        'project': 'v6iphone',
        'rate': '1',
        'rid': '',
        'ruid': room_id,
    }
    api = 'https://v.6.cn/coop/mobile/index.php?padapi=coop-mobile-inroom.php'
    json_str = await async_req(api, data=data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    flv_title = json_data['content']['liveinfo']['flvtitle']
    anchor_name = json_data['content']['roominfo']['alias']
    result = {"anchor_name": anchor_name, "is_live": False}
    if flv_title:
        flv_url = f'https://wlive.6rooms.com/httpflv/{flv_title}.flv'
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result
