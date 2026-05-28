# -*- encoding: utf-8 -*-

import json

from .base import OptionalStr, trace_error_decorator, async_req, get_params


@trace_error_decorator
async def get_shopee_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://live.shopee.sg/share?from=live&session=802458&share_user_id=',
        'user-agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
    }

    if cookies:
        headers['Cookie'] = cookies

    result = {"anchor_name": "", "is_live": False}
    is_living = False

    if 'live.shopee' not in url and 'uid' not in url:
        url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True, abroad=True)

    if 'live.shopee' in url:
        host_suffix = url.split('/')[2].rsplit('.', maxsplit=1)[1]
        is_living = get_params(url, 'uid') is None
    else:
        host_suffix = url.split('/')[2].split('.', maxsplit=1)[0]

    uid = get_params(url, 'uid')
    api_host = f'https://live.shopee.{host_suffix}'
    session_id = get_params(url, 'session')
    if uid:
        json_str = await async_req(f'{api_host}/api/v1/shop_page/live/ongoing?uid={uid}',
                           proxy_addr=proxy_addr, headers=headers, abroad=True)
        json_data = json.loads(json_str)
        if json_data['data']['ongoing_live']:
            session_id = json_data['data']['ongoing_live']['session_id']
            is_living = True
        else:
            json_str = await async_req(f'{api_host}/api/v1/shop_page/live/replay_list?offset=0&limit=1&uid={uid}',
                               proxy_addr=proxy_addr, headers=headers, abroad=True)
            json_data = json.loads(json_str)
            if json_data['data']['replay']:
                result['anchor_name'] = json_data['data']['replay'][0]['nick_name']
                return result

    json_str = await async_req(f'{api_host}/api/v1/session/{session_id}', proxy_addr=proxy_addr, headers=headers, abroad=True)
    json_data = json.loads(json_str)
    if not json_data.get('data'):
        print("Fetch shopee live data failed, please update the address of the live broadcast room and try again.")
        return result
    uid = json_data['data']['session']['uid']
    anchor_name = json_data['data']['session']['nickname']
    live_status = json_data['data']['session']['status']
    result["anchor_name"] = anchor_name
    result['uid'] = f'uid={uid}&session={session_id}'
    if live_status == 1 and is_living:
        flv_url = json_data['data']['session']['play_url']
        title = json_data['data']['session']['title']
        result |= {'is_live': True, 'title': title, 'flv_url': flv_url, 'record_url': flv_url}
    return result
