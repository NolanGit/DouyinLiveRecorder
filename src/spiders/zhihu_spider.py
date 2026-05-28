# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_zhihu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'people/' in url:
        user_id = url.split('people/')[1]
        api = f'https://api.zhihu.com/people/{user_id}/profile?profile_new_version='
        json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        live_page_url = json_data['drama']['living_theater']['theater_url']
    else:
        live_page_url = url

    web_id = live_page_url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    html_str = await async_req(live_page_url, proxy_addr=proxy_addr, headers=headers)
    json_str2 = re.findall('<script id="js-initialData" type="text/json">(.*?)</script>', html_str)[0]
    json_data2 = json.loads(json_str2)
    live_data = json_data2['initialState']['theater']['theaters'][web_id]
    anchor_name = live_data['actor']['name']
    live_status = live_data['drama']['status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        live_title = live_data['theme']
        play_url = live_data['drama']['playInfo']
        result |= {
            'is_live': True,
            'title': live_title,
            'm3u8_url': play_url['hlsUrl'],
            'flv_url': play_url['playUrl'],
            'record_url': play_url['hlsUrl']
        }
    return result
