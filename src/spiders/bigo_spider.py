# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_bigo_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://www.bigo.tv/',
    }
    if cookies:
        headers['Cookie'] = cookies

    if 'bigo.tv' not in url:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
        web_url = re.search(
            '<meta data-n-head="ssr" data-hid="al:web:url" property="al:web:url" content="(.*?)">',
            html_str).group(1)
        room_id = web_url.split('&amp;h=')[-1]
    else:
        if '&h=' in url:
            room_id = url.split('&h=')[-1]
        else:
            room_id = url.split("?")[0].rsplit("/", maxsplit=1)[-1]

    data = {'siteId': room_id}  # roomId
    url2 = 'https://ta.bigo.tv/official_website/studio/getInternalStudioInfo'
    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, data=data)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['nick_name']
    live_status = json_data['data']['alive']
    result = {"anchor_name": anchor_name, "is_live": False}

    if live_status == 1:
        live_title = json_data['data']['roomTopic']
        m3u8_url = json_data['data']['hls_src']
        result['m3u8_url'] = m3u8_url
        result['record_url'] = m3u8_url
        result |= {"title": live_title, "is_live": True, "m3u8_url": m3u8_url, 'record_url': m3u8_url}
    elif result['anchor_name'] == '':
        html_str = await async_req(url=f'https://www.bigo.tv/{url.split("/")[3]}/{room_id}',
                                   proxy_addr=proxy_addr, headers=headers)
        match_anchor_name = re.search('<title>欢迎来到(.*?)的直播间</title>', html_str, re.DOTALL)
        if match_anchor_name:
            anchor_name = match_anchor_name.group(1)
        else:
            match_anchor_name = re.search('<meta data-n-head="ssr" data-hid="og:title" property="og:title" '
                                          'content="(.*?) - BIGO LIVE">', html_str, re.DOTALL)
            anchor_name = match_anchor_name.group(1)
        result['anchor_name'] = anchor_name

    return result
