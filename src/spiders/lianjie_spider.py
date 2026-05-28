# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_lianjie_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        }

    if cookies:
        headers['cookie'] = cookies

    room_id = url.split('?')[0].rsplit('lailianjie.com/', maxsplit=1)[-1]
    play_api = f'https://api.lailianjie.com/ApiServices/service/live/getRoomInfo?&_$t=&_sign=&roomNumber={room_id}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    room_data = json_data['data']
    anchor_name = room_data['nickname']
    live_status = room_data['isonline']

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        title = room_data['defaultRoomTitle']
        webrtc_url = room_data['videoUrl']
        https_url = "https://" + webrtc_url.split('webrtc://')[1]
        flv_url = https_url.replace('?', '.flv?')
        m3u8_url = https_url.replace('?', '.m3u8?')
        result |= {'is_live': True, 'title': title, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result
