# -*- encoding: utf-8 -*-

import json
import re
import urllib.parse

from .base import OptionalStr, trace_error_decorator, async_req, get_params


@trace_error_decorator
async def get_jd_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'origin': 'https://lives.jd.com',
        'referer': 'https://lives.jd.com/',
        'x-referer-page': 'https://lives.jd.com/',
    }

    if cookies:
        headers['Cookie'] = cookies

    redirect_url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)
    author_id = get_params(redirect_url, 'authorId')
    result = {"anchor_name": '', "is_live": False}
    if not author_id:
        live_id = re.search('#/(.*?)\\?origin', redirect_url)
        if not live_id:
            return result
        live_id = live_id.group(1)
        result['anchor_name'] = f'jd_{live_id}'
    else:
        data = {
            'functionId': 'talent_head_findTalentMsg',
            'appid': 'dr_detail',
            'body': '{"authorId":"' + author_id + '","monitorSource":"1","userId":""}',
        }
        info_api = 'https://api.m.jd.com/talent_head_findTalentMsg'
        json_str = await async_req(info_api, data=data, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        anchor_name = json_data['result']['talentName']
        result['anchor_name'] = anchor_name
        if 'livingRoomJump' not in json_data['result']:
            return result
        live_id = json_data['result']['livingRoomJump']['params']['id']
    params = {
        "body": '{"liveId": "' + live_id + '"}',
        "functionId": "getImmediatePlayToM",
        "appid": "h5-live"
    }

    api = f'https://api.m.jd.com/client.action?{urllib.parse.urlencode(params)}'
    # backup_api: https://api.m.jd.com/api
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_status = json_data['data']['status']
    if live_status == 1:
        if author_id:
            data = {
                'functionId': 'jdTalentContentList',
                'appid': 'dr_detail',
                'body': '{"authorId":"' + author_id + '","type":1,"userId":"","page":1,"offset":"-1",'
                                                      '"monitorSource":"1","pageSize":1}',
            }
            json_str2 = await async_req('https://api.m.jd.com/jdTalentContentList', data=data,
                                proxy_addr=proxy_addr, headers=headers)
            json_data2 = json.loads(json_str2)
            result['title'] = json_data2['result']['content'][0]['title']

        flv_url = json_data['data']['videoUrl']
        m3u8_url = json_data['data']['h5VideoUrl']
        result |= {"is_live": True, "m3u8_url": m3u8_url, "flv_url": flv_url, "record_url": m3u8_url}
    return result
