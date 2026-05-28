# -*- encoding: utf-8 -*-

import json
import subprocess
import time
import urllib.parse
import uuid

import execjs

from .base import OptionalStr, trace_error_decorator, async_req, JS_SCRIPT_PATH


@trace_error_decorator
async def get_migu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
            'origin': 'https://www.miguvideo.com',
            'referer': 'https://www.miguvideo.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'appCode': 'miguvideo_default_www',
            'appId': 'miguvideo',
            'channel': 'H5',
        }

    if cookies:
        headers['Cookie'] = cookies

    web_id = url.split('?')[0].rsplit('/')[-1]
    api = f'https://vms-sc.miguvideo.com/vms-match/v6/staticcache/basic/basic-data/{web_id}/miguvideo'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    anchor_name = json_data['body']['title']
    live_title = json_data['body'].get('title') + '-' + json_data['body'].get('detailPageTitle', '')
    room_id = json_data['body'].get('pId')

    result = {"anchor_name": anchor_name, "is_live": False}
    if not room_id:
        return result

    params = {
        'contId': room_id,
        'rateType': '3',
        'clientId': str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'flvEnable': 'true',
        'xh265': 'false',
        'chip': 'mgwww',
        'channelId': '',
    }

    api = f'https://webapi.miguvideo.com/gateway/playurl/v3/play/playurl?{urllib.parse.urlencode(params)}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    live_status = json_data['body']['content']['currentLive']
    if live_status != '1':
        return result
    else:
        result['title'] = live_title
        source_url = json_data['body']['urlInfo']['url']

        async def _get_dd_calcu(url):
            try:
                result = subprocess.run(
                    ["node", f"{JS_SCRIPT_PATH}/migu.js", url],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except execjs.ProgramError:
                raise execjs.ProgramError('Failed to execute JS code. Please check if the Node.js environment')

        ddCalcu = await _get_dd_calcu(source_url)
        real_source_url = f'{source_url}&ddCalcu={ddCalcu}&sv=10010'
        if '.m3u8' in real_source_url:
            m3u8_url = await async_req(
                real_source_url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)
            result['m3u8_url'] = m3u8_url
            result['record_url'] = m3u8_url
        else:
            result['flv_url'] = real_source_url
            result['record_url'] = real_source_url
        result['is_live'] = True
    return result
