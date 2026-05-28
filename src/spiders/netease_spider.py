# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_netease_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://cc.163.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies
    url = url + '/' if url[-1] != '/' else url

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    json_str = re.search('<script id="__NEXT_DATA__" .* crossorigin="anonymous">(.*?)</script></body>',
                         html_str, re.DOTALL).group(1)
    json_data = json.loads(json_str)
    room_data = json_data['props']['pageProps']['roomInfoInitData']
    live_data = room_data['live']
    result = {"is_live": False}
    live_status = live_data.get('status') == 1
    result["anchor_name"] = live_data.get('nickname', room_data.get('nickname'))
    if live_status:
        result |= {
            'is_live': True,
            'title': live_data['title'],
            'stream_list': live_data.get('quickplay'),
            'm3u8_url': live_data.get('sharefile')
        }
    return result
