# -*- encoding: utf-8 -*-

import json
import time
import urllib.parse

import execjs

from .base import OptionalStr, trace_error_decorator, async_req, JS_SCRIPT_PATH, IOS_UA


# 模块加载时一次性读取并编译 JS，避免每次直播探测都重新 open/read/compile
_HAIXIU_JS = execjs.compile(open(f'{JS_SCRIPT_PATH}/haixiu.js').read())


@trace_error_decorator
async def get_haixiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.haixiutv.com',
        'referer': 'https://www.haixiutv.com/',
        'user-agent': IOS_UA,
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split("?")[0].rsplit('/', maxsplit=1)[-1]
    if 'haixiutv' in url:
        access_token = "pLXSC%252FXJ0asc1I21tVL5FYZhNJn2Zg6d7m94umCnpgL%252BuVm31GQvyw%253D%253D"
    else:
        access_token = "s7FUbTJ%252BjILrR7kicJUg8qr025ZVjd07DAnUQd8c7g%252Fo4OH9pdSX6w%253D%253D"

    params = {
        "accessToken": access_token,
        "tku": "3000006",
        "c": "10138100100000",
        "_st1": int(time.time() * 1000)
    }
    ajax_data = _HAIXIU_JS.call('sign', params, f'{JS_SCRIPT_PATH}/crypto-js.min.js')

    params["accessToken"] = urllib.parse.unquote(urllib.parse.unquote(access_token))
    params['_ajaxData1'] = ajax_data
    params['_'] = int(time.time() * 1000)

    if 'haixiutv' in url:
        api = f'https://service.haixiutv.com/v2/room/{room_id}/media/advanceInfoRoom?{urllib.parse.urlencode(params)}'
    else:
        headers['origin'] = 'https://www.lehaitv.com'
        headers['referer'] = 'https://www.lehaitv.com'
        api = f'https://service.lehaitv.com/v2/room/{room_id}/media/advanceInfoRoom?{urllib.parse.urlencode(params)}'

    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)

    stream_data = json_data['data']
    anchor_name = stream_data['nickname']
    live_status = stream_data['live_status']
    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        flv_url = stream_data['media_url_web']
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result
