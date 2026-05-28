# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, trace_error_decorator, async_req
from .twitch_spider import get_twitchtv_stream_data


@trace_error_decorator
async def get_faceit_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Referer': 'https://www.faceit.com/zh/players/qpjzz/stream',
        'faceit-referer': 'web-next',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies
    nickname = re.findall('/players/(.*?)/stream', url)[0]
    api = f'https://www.faceit.com/api/users/v1/nicknames/{nickname}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    user_id = json_data['payload']['id']
    api2 = f'https://www.faceit.com/api/stream/v1/streamings?userId={user_id}'
    json_str2 = await async_req(api2, proxy_addr=proxy_addr, headers=headers)
    json_data2 = json.loads(json_str2)
    platform_info = json_data2['payload'][0]
    anchor_name = platform_info.get('userNickname')
    anchor_id = platform_info.get('platformId')
    platform = platform_info.get('platform')
    if platform == 'twitch':
        result = await get_twitchtv_stream_data(f'https://www.twitch.tv/{anchor_id}')
        result['anchor_name'] = anchor_name
    else:
        result = {'anchor_name': anchor_name, 'is_live': False}
    return result
