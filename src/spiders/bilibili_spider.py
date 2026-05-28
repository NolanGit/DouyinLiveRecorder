# -*- encoding: utf-8 -*-

import json
import urllib.parse
from operator import itemgetter

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_bilibili_room_info_h5(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> str:
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36',
        'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'cookie': '',
        'origin': 'https://live.bilibili.com',
        'referer': 'https://live.bilibili.com/26066074',
    }
    if cookies:
        headers['cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    api = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getH5InfoByRoom?room_id={room_id}'
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    room_info = json.loads(json_str)
    title = room_info['data']['room_info'].get('title') if room_info.get('data') else ''
    return title


@trace_error_decorator
async def get_bilibili_room_info(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }
    if cookies:
        headers['Cookie'] = cookies

    try:
        room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
        json_str = await async_req(f'https://api.live.bilibili.com/room/v1/Room/room_init?id={room_id}',
                           proxy_addr=proxy_addr, headers=headers)
        room_info = json.loads(json_str)
        uid = room_info['data']['uid']
        live_status = True if room_info['data']['live_status'] == 1 else False

        api = f'https://api.live.bilibili.com/live_user/v1/Master/info?uid={uid}'
        json_str2 = await async_req(url=api, proxy_addr=proxy_addr, headers=headers)
        anchor_info = json.loads(json_str2)
        anchor_name = anchor_info['data']['info']['uname']

        title = await get_bilibili_room_info_h5(url, proxy_addr, cookies)
        return {"anchor_name": anchor_name, "live_status": live_status, "room_url": url, "title": title}
    except Exception as e:
        print(e)
        return {"anchor_name": '', "live_status": False, "room_url": url}


@trace_error_decorator
async def get_bilibili_stream_data(url: str, qn: str = '10000', platform: str = 'web', proxy_addr: OptionalStr = None,
                             cookies: OptionalStr = None) -> OptionalStr:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'origin': 'https://live.bilibili.com',
        'referer': 'https://live.bilibili.com/26066074',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[1]
    params = {
        'cid': room_id,
        'qn': qn,
        'platform': platform,
    }
    play_api = f'https://api.live.bilibili.com/room/v1/Room/playUrl?{urllib.parse.urlencode(params)}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    if json_data and json_data['code'] == 0:
        for i in json_data['data']['durl']:
            if 'd1--cn-gotcha' in i['url']:
                return i['url']
        return json_data['data']['durl'][-1]['url']
    else:
        params = {
            "room_id": room_id,
            "protocol": "0,1",
            "format": "0,1,2",
            "codec": "0,1,2",
            "qn": qn,
            "platform": "web",
            "ptype": "8",
            "dolby": "5",
            "panorama": "1",
            "hdr_type": "0,1"
        }

        # 此接口因网页上有限制, 需要配置登录后的cookie才能获取最高画质
        api = f'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?{urllib.parse.urlencode(params)}'
        json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_data = json.loads(json_str)
        if json_data['data']['live_status'] == 0:
            print("The anchor did not start broadcasting.")
            return
        playurl_info = json_data['data']['playurl_info']
        format_list = playurl_info['playurl']['stream'][0]['format']
        stream_data_list = format_list[0]['codec']
        sorted_stream_list = sorted(stream_data_list, key=itemgetter("current_qn"), reverse=True)
        # qn: 30000=杜比 20000=4K 10000=原画 400=蓝光 250=超清 150=高清 80=流畅
        video_quality_options = {'10000': 0, '400': 1, '250': 2, '150': 3, '80': 4}
        qn_count = len(sorted_stream_list)
        select_stream_index = min(video_quality_options[qn], qn_count - 1)
        stream_data: dict = sorted_stream_list[select_stream_index]
        base_url = stream_data['base_url']
        host = stream_data['url_info'][0]['host']
        extra = stream_data['url_info'][0]['extra']
        m3u8_url = host + base_url + extra
        return m3u8_url
