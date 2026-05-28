# -*- encoding: utf-8 -*-

import json
import urllib.parse

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_liuxing_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Referer': 'https://wap.7u66.com/198189?promoters=0',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',

    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    params = {
        "promoters": "0",
        "roomidx": room_id,
        "currentUrl": f"https://www.7u66.com/{room_id}?promoters=0"
    }
    api = f'https://wap.7u66.com/api/ui/room/v1.0.0/live.ashx?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    room_info = json_data['data']['roomInfo']
    anchor_name = room_info['nickname']
    live_status = room_info["live_stat"]
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        idx = room_info['idx']
        live_id = room_info['liveId1']
        flv_url = f'https://txpull1.5see.com/live/{idx}/{live_id}.flv'
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result
