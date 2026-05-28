# -*- encoding: utf-8 -*-

import json
import re
import time
import urllib.parse

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_yy_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://www.yy.com/',
        'Cookie': 'hd_newui=0.2103068903976506; hdjs_session_id=0.4929014850884579; hdjs_session_time=1694004002636; hiido_ui=0.923076230899782'
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    anchor_name = re.search('nick: "(.*?)",\n\\s+logo', html_str).group(1)
    cid = re.search('sid : "(.*?)",\n\\s+ssid', html_str, re.DOTALL).group(1)

    data = '{"head":{"seq":1701869217590,"appidstr":"0","bidstr":"121","cidstr":"' + cid + '","sidstr":"' + cid + '","uid64":0,"client_type":108,"client_ver":"5.17.0","stream_sys_ver":1,"app":"yylive_web","playersdk_ver":"5.17.0","thundersdk_ver":"0","streamsdk_ver":"5.17.0"},"client_attribute":{"client":"web","model":"web0","cpu":"","graphics_card":"","os":"chrome","osversion":"0","vsdk_version":"","app_identify":"","app_version":"","business":"","width":"1920","height":"1080","scale":"","client_type":8,"h265":0},"avp_parameter":{"version":1,"client_type":8,"service_type":0,"imsi":0,"send_time":1701869217,"line_seq":-1,"gear":4,"ssl":1,"stream_format":0}}'
    data_bytes = data.encode('utf-8')
    params = {
        "uid": "0",
        "cid": cid,
        "sid": cid,
        "appid": "0",
        "sequence": "1701869217590",
        "encode": "json"
    }
    url2 = f'https://stream-manager.yy.com/v3/channel/streams?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=url2, data=data_bytes, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    json_data['anchor_name'] = anchor_name

    params = {
        'uid': '',
        'sid': cid,
        'ssid': cid,
        '_': int(time.time() * 1000),
    }
    detail_api = f'https://www.yy.com/live/detail?{urllib.parse.urlencode(params)}'
    json_str2 = await async_req(detail_api, proxy_addr=proxy_addr, headers=headers)
    json_data2 = json.loads(json_str2)
    json_data['title'] = json_data2['data']['roomName']
    return json_data
