# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_picarto_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        }

    if cookies:
        headers['cookie'] = cookies

    anchor_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    api = f'https://ptvintern.picarto.tv/api/channel/detail/{anchor_id}'

    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    anchor_name = json_data['channel']['name']
    live_status = json_data['channel']['online']

    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        title = json_data['channel']['title']
        m3u8_url = f"https://1-edge1-us-newyork.picarto.tv/stream/hls/golive+{anchor_name}/index.m3u8"
        result |= {'is_live': True, 'title': title, 'm3u8_url': m3u8_url, 'record_url': m3u8_url}
    return result
