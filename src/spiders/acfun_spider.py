# -*- encoding: utf-8 -*-

import json
import urllib.parse
from operator import itemgetter

from .base import OptionalStr, async_req, trace_error_decorator, utils


@trace_error_decorator
async def get_acfun_sign_params(proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    did = f'web_{utils.generate_random_string(16)}'
    headers = {
        'referer': 'https://live.acfun.cn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'cookie': f'_did={did};',
    }
    if cookies:
        headers['Cookie'] = cookies
    data = {
        'sid': 'acfun.api.visitor',
    }
    api = 'https://id.app.acfun.cn/rest/app/visitor/login'
    json_str = await async_req(api, data=data, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    user_id = json_data["userId"]
    visitor_st = json_data["acfun.api.visitor_st"]
    return user_id, did, visitor_st


@trace_error_decorator
async def get_acfun_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'referer': 'https://live.acfun.cn/live/17912421',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    author_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    user_info_api = f'https://live.acfun.cn/rest/pc-direct/user/userInfo?userId={author_id}'
    json_str = await async_req(user_info_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['profile']['name']
    status = 'liveId' in json_data['profile']
    result = {"anchor_name": anchor_name, "is_live": False}
    if status:
        result["is_live"] = True
        user_id, did, visitor_st = await get_acfun_sign_params(proxy_addr=proxy_addr, cookies=cookies)
        params = {
            'subBiz': 'mainApp',
            'kpn': 'ACFUN_APP',
            'kpf': 'PC_WEB',
            'userId': user_id,
            'did': did,
            'acfun.api.visitor_st': visitor_st,
        }

        data = {
            'authorId': author_id,
            'pullStreamType': 'FLV',
        }
        play_api = f'https://api.kuaishouzt.com/rest/zt/live/web/startPlay?{urllib.parse.urlencode(params)}'
        json_str = await async_req(play_api, data=data, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        live_title = json_data['data']['caption']
        videoPlayRes = json_data['data']['videoPlayRes']
        play_url_list = json.loads(videoPlayRes)['liveAdaptiveManifest'][0]['adaptationSet']['representation']
        play_url_list = sorted(play_url_list, key=itemgetter('bitrate'), reverse=True)
        result |= {'play_url_list': play_url_list, 'title': live_title}
    return result
