# -*- encoding: utf-8 -*-

import json
import re
import time
import urllib.parse

from .base import OptionalStr, OptionalDict, async_req, trace_error_decorator, utils, script_path


async def get_huajiao_sn(url: str, cookies: OptionalStr = None, proxy_addr: OptionalStr = None) -> tuple | None:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.huajiao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies

    live_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    api = f'https://www.huajiao.com/l/{live_id}'
    try:
        html_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
        json_str = re.search('var feed = (.*?});', html_str).group(1)
        json_data = json.loads(json_str)
        sn = json_data['feed']['sn']
        uid = json_data['author']['uid']
        nickname = json_data['author']['nickname']
        live_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
        return nickname, sn, uid, live_id
    except Exception:
        utils.replace_url(f'{script_path}/config/URL_config.ini', old=url, new='#' + url)
        raise RuntimeError("Failed to retrieve live room data, the Huajiao live room address is not fixed, please use "
                           "the anchor's homepage address for recording.")


async def get_huajiao_user_info(url: str, cookies: OptionalStr = None, proxy_addr: OptionalStr = None) -> OptionalDict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.huajiao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }

    if cookies:
        headers['Cookie'] = cookies

    if 'user' in url:
        uid = url.split('?')[0].split('user/')[1]
        params = {
            'uid': uid,
            'fmt': 'json',
            '_': str(int(time.time() * 1000)),
        }

        api = f'https://webh.huajiao.com/User/getUserFeeds?{urllib.parse.urlencode(params)}'
        json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)

        html_str = await async_req(url=f'https://www.huajiao.com/user/{uid}', proxy_addr=proxy_addr, headers=headers)
        anchor_name = re.search('<title>(.*?)的主页.*</title>', html_str).group(1)
        if json_data['data'] and 'sn' in json_data['data']['feeds'][0]['feed']:
            feed = json_data['data']['feeds'][0]['feed']
            return {
                "anchor_name": anchor_name,
                "title": feed['title'],
                "is_live": True,
                "sn": feed['sn'],
                "liveid": feed['relateid'],
                "uid": uid
            }
        else:
            return {"anchor_name": anchor_name, "is_live": False}


async def get_huajiao_stream_url_app(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> OptionalDict:
    headers = {
        'User-Agent': 'living/9.4.0 (com.huajiao.seeding; build:2410231746; iOS 17.0.0) Alamofire/9.4.0',
        'accept-language': 'zh-Hans-US;q=1.0',
        'sdk_version': '1',
    }
    if cookies:
        headers['Cookie'] = cookies
    room_id = url.rsplit('/', maxsplit=1)[1]
    api = f'https://live.huajiao.com/feed/getFeedInfo?relateid={room_id}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    if json_data['errmsg'] or not json_data['data'].get('creatime'):
        print("Failed to retrieve live room data, the Huajiao live room address is not fixed, please manually change "
              "the address for recording.")
        return
    data = json_data['data']
    return {
        "anchor_name": data['author']['nickname'],
        "title": data['feed']['title'],
        "is_live": True,
        "sn": data['feed']['sn'],
        "liveid": data['feed']['relateid'],
        "uid": data['author']['uid']
    }


@trace_error_decorator
async def get_huajiao_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://www.huajiao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    result = {"anchor_name": "", "is_live": False}

    if 'user/' in url:
        if not cookies:
            return result
        room_data = await get_huajiao_user_info(url, cookies, proxy_addr)
    else:
        url = await async_req(url, proxy_addr=proxy_addr, headers=headers, redirect_url=True)
        if url.rstrip('/') == 'https://www.huajiao.com':
            print(
                "Failed to retrieve live room data, the Huajiao live room address is not fixed, please manually change "
                "the address for recording.")
            return result
        room_data = await get_huajiao_stream_url_app(url, proxy_addr)

    if room_data:
        result["anchor_name"] = room_data.pop("anchor_name")
        live_status = room_data.pop("is_live")

        if live_status:
            result["title"] = room_data.pop("title")
            params = {
                "time": int(time.time() * 1000),
                "version": "1.0.0",
                **room_data,
                "encode": "h265"
            }

            api = f'https://live.huajiao.com/live/substream?{urllib.parse.urlencode(params)}'
            json_str = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
            json_data = json.loads(json_str)
            result |= {
                'is_live': True,
                'flv_url': json_data['data']['h264_url'],
                'record_url': json_data['data']['h264_url'],
            }
    return result
