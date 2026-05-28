# -*- encoding: utf-8 -*-

import json
import random
import re
import time
import urllib.parse

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_baidu_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Referer': 'https://live.baidu.com/',
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }
    if cookies:
        headers['Cookie'] = cookies

    uid = random.choice([
        'h5-683e85bdf741bf2492586f7ca39bf465',
        'h5-c7c6dc14064a136be4215b452fab9eea',
        'h5-4581281f80bb8968bd9a9dfba6050d3a'
    ])
    room_id = re.search('room_id=(.*?)&', url).group(1)
    params = {
        'cmd': '371',
        'action': 'star',
        'service': 'bdbox',
        'osname': 'baiduboxapp',
        'data': '{"data":{"room_id":"' + room_id + '","device_id":"h5-683e85bdf741bf2492586f7ca39bf465",'
                                                   '"source_type":0,"osname":"baiduboxapp"},"replay_slice":0,'
                                                   '"nid":"","schemeParams":{"src_pre":"pc","src_suf":"other",'
                                                   '"bd_vid":"","share_uid":"","share_cuk":"","share_ecid":"",'
                                                   '"zb_tag":"","shareTaskInfo":"{\\"room_id\\":\\"9175031377\\"}",'
                                                   '"share_from":"","ext_params":"","nid":""}}',
        'ua': '360_740_ANDROID_0',
        'bd_vid': '',
        'uid': uid,
        '_': str(int(time.time() * 1000)),
    }
    app_api = f'https://mbd.baidu.com/searchbox?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=app_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    key = list(json_data['data'].keys())[0]
    data = json_data['data'][key]
    anchor_name = data['host']['name']
    result = {"anchor_name": anchor_name, "is_live": False}
    if data['status'] == "0":
        result["is_live"] = True
        live_title = data['video']['title']
        play_url_list = data['video']['url_clarity_list']
        url_list = []
        prefix = 'https://hls.liveshow.bdstatic.com/live/'
        if play_url_list:
            for i in play_url_list:
                url_list.append(
                    prefix + i['urls']['flv'].rsplit('.', maxsplit=1)[0].rsplit('/', maxsplit=1)[1] + '.m3u8')
        else:
            play_url_list = data['video']['url_list']
            for i in play_url_list:
                url_list.append(prefix + i['urls'][0]['hls'].rsplit('?', maxsplit=1)[0].rsplit('/', maxsplit=1)[1])

        if url_list:
            result |= {"is_live": True, "title": live_title, 'play_url_list': url_list}
    return result
