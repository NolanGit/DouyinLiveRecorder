# -*- encoding: utf-8 -*-

import json
import re
import time
import urllib.parse

import execjs

from .base import OptionalStr, trace_error_decorator, async_req, get_params, JS_SCRIPT_PATH, utils


@trace_error_decorator
async def get_taobao_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'Referer': 'https://huodong.m.taobao.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Cookie': '',
    }

    if cookies:
        headers['Cookie'] = cookies

    if '_m_h5_tk' not in headers['Cookie']:
        print('Error: Cookies is empty! please input correct cookies')

    live_id = get_params(url, 'id')
    if not live_id:
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
        redirect_url = re.findall("var url = '(.*?)';", html_str)[0]
        live_id = get_params(redirect_url, 'id')

    params = {
        'jsv': '2.7.0',
        'appKey': '12574478',
        't': '1733104933120',
        'sign': '',
        'AntiFlood': 'true',
        'AntiCreep': 'true',
        'api': 'mtop.mediaplatform.live.livedetail',
        'v': '4.0',
        'preventFallback': 'true',
        'type': 'jsonp',
        'dataType': 'jsonp',
        'callback': 'mtopjsonp1',
        'data': '{"liveId":"' + live_id + '","creatorId":null}',
    }

    for i in range(2):
        app_key = '12574478'
        _m_h5_tk = re.findall('_m_h5_tk=(.*?);', headers['Cookie'])[0]
        t13 = int(time.time() * 1000)
        pre_sign_str = f'{_m_h5_tk.split("_")[0]}&{t13}&{app_key}&' + params['data']
        sign = execjs.compile(open(f'{JS_SCRIPT_PATH}/taobao-sign.js').read()).call('sign', pre_sign_str)
        params |= {'sign': sign, 't': t13}
        api = f'https://h5api.m.taobao.com/h5/mtop.mediaplatform.live.livedetail/4.0/?{urllib.parse.urlencode(params)}'
        jsonp_str, new_cookie = await async_req(url=api, proxy_addr=proxy_addr, headers=headers, timeout=20,
                                                return_cookies=True, include_cookies=True)
        json_data = utils.jsonp_to_json(jsonp_str)

        ret_msg = json_data['ret']
        if ret_msg == ['SUCCESS::调用成功']:
            anchor_name = json_data['data']['broadCaster']['accountName']
            result = {"anchor_name": anchor_name, "is_live": False}
            live_status = json_data['data']['streamStatus']
            if live_status == '1':
                live_title = json_data['data']['title']
                play_url_list = json_data['data']['liveUrlList']

                def get_sort_key(item):
                    definition_priority = {
                        "lld": 0, "ld": 1, "md": 2, "hd": 3, "ud": 4
                    }
                    def_value = item.get('definition') or item.get('newDefinition')
                    priority = definition_priority.get(def_value, -1)
                    return priority

                play_url_list = sorted(play_url_list, key=get_sort_key, reverse=True)
                result |= {"is_live": True, "title": live_title, "play_url_list": play_url_list, 'live_id': live_id}

            return result
        else:
            print(f'Error: Taobao live data fetch failed, {ret_msg[0]}')

        if '_m_h5_tk' in new_cookie and '_m_h5_tk_enc' in new_cookie:
            headers['Cookie'] = re.sub('_m_h5_tk=(.*?);', new_cookie['_m_h5_tk'], headers['Cookie'])
            headers['Cookie'] = re.sub('_m_h5_tk_enc=(.*?);', new_cookie['_m_h5_tk_enc'], headers['Cookie'])
        else:
            print('Error: Try to update cookie failed, please update the cookies in the configuration file')
