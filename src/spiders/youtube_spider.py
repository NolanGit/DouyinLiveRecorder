# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, trace_error_decorator, async_req, get_play_url_list


@trace_error_decorator
async def get_youtube_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_str = re.search('var ytInitialPlayerResponse = (.*?);var meta = document\\.createElement', html_str).group(1)
    json_data = json.loads(json_str)
    result = {"anchor_name": "", "is_live": False}
    if 'videoDetails' not in json_data:
        print("Error: Please log in to YouTube on your device's webpage and configure cookies in the config.ini")
        return result
    result['anchor_name'] = json_data['videoDetails']['author']
    live_status = json_data['videoDetails'].get('isLive')
    if live_status:
        live_title = json_data['videoDetails']['title']
        m3u8_url = json_data['streamingData']["hlsManifestUrl"]
        play_url_list = await get_play_url_list(m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        result |= {"is_live": True, "title": live_title, "m3u8_url": m3u8_url, "play_url_list": play_url_list}
    return result
