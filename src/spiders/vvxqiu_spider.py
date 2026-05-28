# -*- encoding: utf-8 -*-

import json
import urllib.parse

from .base import OptionalStr, trace_error_decorator, async_req, get_params


@trace_error_decorator
async def get_vvxqiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Access-Control-Request-Method': 'GET',
        'Origin': 'https://h5webcdn-pro.vvxqiu.com',
        'Referer': 'https://h5webcdn-pro.vvxqiu.com/',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = get_params(url, "roomId")
    api_1 = f'https://h5p.vvxqiu.com/activity-center/fanclub/activity/captain/banner?roomId={room_id}&product=vvstar'
    json_str = await async_req(api_1, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['anchorName']
    if not anchor_name:
        params = {
            'sessionId': '',
            'userId': '',
            'product': 'vvstar',
            'tickToken': '',
            'roomId': room_id,
        }
        json_str = await async_req(
            f'https://h5p.vvxqiu.com/activity-center/halloween2023/banner?{urllib.parse.urlencode(params)}',
            proxy_addr=proxy_addr, headers=headers
        )
        json_data = json.loads(json_str)
        anchor_name = json_data['data']['memberVO']['memberName']

    result = {"anchor_name": anchor_name, "is_live": False}
    m3u8_url = f'https://liveplay-pro.wasaixiu.com/live/1400442770_{room_id}_{room_id[2:]}_single.m3u8'
    resp = await async_req(m3u8_url, proxy_addr=proxy_addr, headers=headers)
    if 'Not Found' not in resp:
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'record_url': m3u8_url}
    return result
