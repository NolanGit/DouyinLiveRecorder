# -*- encoding: utf-8 -*-

import json
import re
import time
import urllib.parse

from .base import OptionalStr, async_req


async def get_kugou_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://fanxing2.kugou.com/',
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'roomId' in url:
        room_id = re.search('roomId=(\\d+)', url).group(1)
    else:
        room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]

    app_api = f'https://service2.fanxing.kugou.com/roomcen/room/web/cdn/getEnterRoomInfo?roomId={room_id}'
    json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['normalRoomInfo']['nickName']
    result = {"anchor_name": anchor_name, "is_live": False}
    if not anchor_name:
        raise RuntimeError(
            "Music channel live rooms are not supported for recording, please switch to a different live room."
        )
    live_status = json_data['data']['liveType']
    if live_status != -1:
        params = {
            'std_rid': room_id,
            'std_plat': '7',
            'std_kid': '0',
            'streamType': '1-2-4-5-8',
            'ua': 'fx-flash',
            'targetLiveTypes': '1-5-6',
            'version': '1000',
            'supportEncryptMode': '1',
            'appid': '1010',
            '_': str(int(time.time() * 1000)),
        }
        api = f'https://fx1.service.kugou.com/video/pc/live/pull/mutiline/streamaddr?{urllib.parse.urlencode(params)}'
        json_str2 = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_data2 = json.loads(json_str2)
        stream_data = json_data2['data']['lines']
        if stream_data:
            flv_url = stream_data[-1]['streamProfiles'][0]['httpsFlv'][0]
            result |= {"is_live": True, "flv_url": flv_url, "record_url": flv_url}
    return result
