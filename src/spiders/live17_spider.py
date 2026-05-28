# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_17live_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://17.live',
        'referer': 'https://17.live/',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    api_1 = f'https://wap-api.17app.co/api/v1/user/room/{room_id}'
    json_str = await async_req(api_1, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data["displayName"]
    result = {"anchor_name": anchor_name, "is_live": False}
    json_data = {
        'liveStreamID': room_id,
    }
    api_1 = f'https://wap-api.17app.co/api/v1/lives/{room_id}/viewers/alive'
    json_str = await async_req(api_1, json_data=json_data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_status = json_data.get("status")
    if live_status and live_status == 2:
        flv_url = json_data['pullURLsInfo']['rtmpURLs'][0]['urlHighQuality']
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result
