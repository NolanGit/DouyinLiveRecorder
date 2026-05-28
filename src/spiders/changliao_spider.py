# -*- encoding: utf-8 -*-

import json
import re
import urllib.parse

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_changliao_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://wap.tlclw.com/phone/15777?promoters=0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    params = {
        'roomidx': room_id,
        'currentUrl': f'https://wap.tlclw.com/{room_id}',
    }
    play_api = f'https://wap.tlclw.com/api/ui/room/v1.0.0/live.ashx?{urllib.parse.urlencode(params)}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['roomInfo']['nickname']
    live_status = json_data['data']['roomInfo']['live_stat']

    async def get_live_domain(page_url):
        html_str = await async_req(page_url, proxy_addr=proxy_addr, headers=headers)
        config_json_str = re.findall("var config = (.*?)config.webskins",
                                     html_str, re.DOTALL)[0].rsplit(";", maxsplit=1)[0].strip()
        config_json_data = json.loads(config_json_str)
        stream_flv_domain = config_json_data['domainpullstream_flv']
        stream_hls_domain = config_json_data['domainpullstream_hls']
        return stream_flv_domain, stream_hls_domain

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_domain, hls_domain = await get_live_domain(url)
        live_id = json_data['data']['roomInfo']['liveID']
        flv_url = f'{flv_domain}/{live_id}.flv'
        m3u8_url = f'{hls_domain}/{live_id}.m3u8'
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': flv_url}
    return result
