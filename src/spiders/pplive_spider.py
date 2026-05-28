# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req, get_params


@trace_error_decorator
async def get_pplive_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://m.pp.weimipopo.com',
        'Referer': 'https://m.pp.weimipopo.com/',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = get_params(url, 'anchorUid')
    json_data = {
        'inviteUuid': '',
        'anchorUuid': room_id,
    }

    if 'catshow' in url:
        api = 'https://api.catshow168.com/live/preview'
        headers['Origin'] = 'https://h.catshow168.com'
        headers['Referer'] = 'https://h.catshow168.com'
    else:
        api = 'https://api.pp.weimipopo.com/live/preview'
    json_str = await async_req(api, json_data=json_data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_info = json_data['data']
    anchor_name = live_info['name']
    live_status = live_info['living']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status:
        m3u8_url = live_info['pullUrl']
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'record_url': m3u8_url}
    return result
