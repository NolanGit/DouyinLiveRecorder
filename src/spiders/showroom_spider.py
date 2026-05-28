# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, async_req, trace_error_decorator, get_play_url_list


@trace_error_decorator
async def get_showroom_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    if '/room/profile' in url:
        room_id = url.split('room_id=')[-1]
    else:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers, abroad=True)
        room_id = re.search('href="/room/profile\\?room_id=(.*?)"', html_str).group(1)
    info_api = f'https://www.showroom-live.com/api/live/live_info?room_id={room_id}'
    json_str = await async_req(info_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    anchor_name = json_data['room_name']
    result = {"anchor_name": anchor_name, "is_live": False}
    live_status = json_data['live_status']
    if live_status == 2:
        result["is_live"] = True
        web_api = f'https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}&abr_available=1'
        json_str = await async_req(web_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
        if json_str:
            json_data = json.loads(json_str)
            streaming_url_list = json_data['streaming_url_list']

            for i in streaming_url_list:
                if i['type'] == 'hls_all':
                    m3u8_url = i['url']
                    result['m3u8_url'] = m3u8_url
                    if m3u8_url:
                        m3u8_url_list = await get_play_url_list(m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
                        if m3u8_url_list:
                            result['play_url_list'] = [f"{m3u8_url.rsplit('/', maxsplit=1)[0]}/{i}" for i in
                                                       m3u8_url_list]
                        else:
                            result['play_url_list'] = [m3u8_url]
                        result['play_url_list'] = [i.replace('https://', 'http://') for i in result['play_url_list']]
                        break
    return result
