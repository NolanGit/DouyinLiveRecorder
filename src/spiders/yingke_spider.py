# -*- encoding: utf-8 -*-

import json
import time
import urllib.parse

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_yingke_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Referer': 'https://www.inke.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    uid = query_params['uid'][0]
    live_id = query_params['id'][0]
    params = {
        'uid': uid,
        'id': live_id,
        '_t': str(int(time.time())),
    }

    api = f'https://webapi.busi.inke.cn/web/live_share_pc?{urllib.parse.urlencode(params)}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['media_info']['nick']
    live_status = json_data['data']['status']

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status == 1:
        m3u8_url = json_data['data']['live_addr'][0]['hls_stream_addr']
        flv_url = json_data['data']['live_addr'][0]['stream_addr']
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'flv_url': flv_url, 'record_url': m3u8_url}
    return result
