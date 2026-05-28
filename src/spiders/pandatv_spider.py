# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, get_params, get_play_url_list, async_req, trace_error_decorator


@trace_error_decorator
async def get_pandatv_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.pandalive.co.kr',
        'referer': 'https://www.pandalive.co.kr/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    user_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    url2 = 'https://api.pandalive.co.kr/v1/live/play'
    data = {
        'userId': user_id,
        'info': 'media fanGrade',
    }
    room_password = get_params(url, "pwd")
    if not room_password:
        room_password = ''
    data2 = {
        'action': 'watch',
        'userId': user_id,
        'password': room_password,
        'shareLinkType': '',
    }

    result = {"anchor_name": "", "is_live": False}
    json_str = await async_req('https://api.pandalive.co.kr/v1/member/bj',
                       proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = json.loads(json_str)
    if "bjInfo" not in json_data:
        raise RuntimeError(json_data.get("message", 'Unknown error'))
    anchor_id = json_data['bjInfo']['id']
    anchor_name = f"{json_data['bjInfo']['nick']}-{anchor_id}"
    result['anchor_name'] = anchor_name
    live_status = 'media' in json_data

    if live_status:
        json_str = await async_req(url2, proxy_addr=proxy_addr, headers=headers, data=data2, abroad=True)
        json_data = json.loads(json_str)
        if 'errorData' in json_data:
            if json_data['errorData']['code'] == 'needAdult':
                raise RuntimeError(f"{url} The live room requires login and is only accessible to adults. Please "
                                   f"correctly fill in the login cookie in the configuration file.")
            else:
                raise RuntimeError(json_data['errorData']['code'], json_data['message'])
        play_url = json_data['PlayList']['hls'][0]['url']
        play_url_list = await get_play_url_list(m3u8=play_url, proxy=proxy_addr, header=headers, abroad=True)
        result |= {'is_live': True, 'm3u8_url': play_url, 'play_url_list': play_url_list}
    return result
