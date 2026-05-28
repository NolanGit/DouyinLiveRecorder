# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req, get_params, get_play_url_list


@trace_error_decorator
async def get_winktv_bj_info(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://www.winktv.co.kr/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies
    user_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    data = {
        'userId': user_id,
        'info': 'media',
    }

    info_api = 'https://api.winktv.co.kr/v1/member/bj'
    json_str = await async_req(url=info_api, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = json.loads(json_str)
    live_status = 'media' in json_data
    anchor_id = json_data['bjInfo']['id']
    anchor_name = f"{json_data['bjInfo']['nick']}-{anchor_id}"
    return anchor_name, live_status


@trace_error_decorator
async def get_winktv_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://www.winktv.co.kr',
        'origin': 'https://www.winktv.co.kr',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',

    }
    if cookies:
        headers['Cookie'] = cookies
    user_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]
    room_password = get_params(url, "pwd")
    if not room_password:
        room_password = ''
    data = {
        'action': 'watch',
        'userId': user_id,
        'password': room_password,
        'shareLinkType': '',
    }

    anchor_name, live_status = await get_winktv_bj_info(url=url, proxy_addr=proxy_addr, cookies=cookies)
    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        play_api = 'https://api.winktv.co.kr/v1/live/play'
        json_str = await async_req(url=play_api, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
        if '403: Forbidden' in json_str:
            raise ConnectionError(f"Your network has been banned from accessing WinkTV ({json_str})")
        json_data = json.loads(json_str)
        if 'errorData' in json_data:
            if json_data['errorData']['code'] == 'needAdult':
                raise RuntimeError(f"{url} The live stream is only accessible to logged-in adults. Please ensure that "
                                   f"the cookie is correctly filled in the configuration file after logging in.")
            else:
                raise RuntimeError(json_data['errorData']['code'], json_data['message'])
        m3u8_url = json_data['PlayList']['hls'][0]['url']
        play_url_list = await get_play_url_list(m3u8=m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        result['m3u8_url'] = m3u8_url
        result['play_url_list'] = play_url_list
    return result
