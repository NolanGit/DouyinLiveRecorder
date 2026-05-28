# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_maoerfm_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://fm.missevan.com/live/868895007',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    url2 = f'https://fm.missevan.com/api/v2/live/{room_id}'

    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    anchor_name = json_data['info']['creator']['username']
    live_status = False
    if 'room' in json_data['info']:
        live_status = json_data['info']['room']['status']['broadcasting']

    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        stream_list = json_data['info']['room']['channel']
        m3u8_url = stream_list['hls_pull_url']
        flv_url = stream_list['flv_pull_url']
        title = json_data['info']['room']['name']
        result |= {'is_live': True, 'title': title, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result
