# -*- encoding: utf-8 -*-

import json
import time
import urllib.parse

import execjs

from .base import OptionalStr, trace_error_decorator, async_req, JS_SCRIPT_PATH


@trace_error_decorator
async def get_haixiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'origin': 'https://www.haixiutv.com',
        'referer': 'https://www.haixiutv.com/',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
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
    ajax_data = execjs.compile(open(f'{JS_SCRIPT_PATH}/haixiu.js').read()).call('sign', params,
                                                                                f'{JS_SCRIPT_PATH}/crypto-js.min.js')

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
