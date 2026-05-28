# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req, get_play_url_list


@trace_error_decorator
async def get_chzzk_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'origin': 'https://chzzk.naver.com',
        'referer': 'https://chzzk.naver.com/live/458f6ec20b034f49e0fc6d03921646d2',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    play_api = f'https://api.chzzk.naver.com/service/v3/channels/{room_id}/live-detail'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    live_data = json_data['content']
    anchor_name = live_data['channel']['channelName']
    live_status = live_data['status']

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 'OPEN':
        play_data = json.loads(live_data['livePlaybackJson'])
        m3u8_url = play_data['media'][0]['path']
        m3u8_url_list = await get_play_url_list(m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        prefix = m3u8_url.split('?')[0].rsplit('/', maxsplit=1)[0]
        m3u8_url_list = [prefix + '/' + i for i in m3u8_url_list]
        result |= {"is_live": True, "m3u8_url": m3u8_url, "play_url_list": m3u8_url_list}
    return result
