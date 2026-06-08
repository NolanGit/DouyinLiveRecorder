# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req, IOS_UA


@trace_error_decorator
async def get_langlive_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.lang.live',
        'referer': 'https://www.lang.live/',
        'user-agent': IOS_UA,
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    api_1 = f'https://api.lang.live/langweb/v1/room/liveinfo?room_id={room_id}'
    json_str = await async_req(api_1, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    live_info = json_data['data']['live_info']
    anchor_name = live_info['nickname']
    live_status = live_info['live_status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_url = json_data['data']['live_info']['liveurl']
        m3u8_url = json_data['data']['live_info']['liveurl_hls']
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': m3u8_url}
    return result
