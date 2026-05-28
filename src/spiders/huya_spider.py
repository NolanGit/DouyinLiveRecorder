# -*- encoding: utf-8 -*-

import json
import re
import urllib.parse

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_huya_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Cookie': 'huya_ua=webh5&0.1.0&websocket; game_did=zXyXVqV1NF4ZeNWg7QaOFbpIEWqcsrxkoVy; alphaValue=0.80; isInLiveRoom=; guid=0a7df378828609654d01a205a305fb52; __yamid_tt1=0.8936157401010706; __yamid_new=CA715E8BC9400001E5A313E028F618DE; udb_guiddata=4657813d32ce43d381ea8ff8d416a3c2; udb_deviceid=w_756598227007868928; sdid=0UnHUgv0_qmfD4KAKlwzhqQB32nywGZJYLZl_9RLv0Lbi5CGYYNiBGLrvNZVszz4FEo_unffNsxk9BdvXKO_PkvC5cOwCJ13goOiNYGClLirWVkn9LtfFJw_Qo4kgKr8OZHDqNnuwg612sGyflFn1draukOt03gk2m3pwGbiKsB143MJhMxcI458jIjiX0MYq; Hm_lvt_51700b6c722f5bb4cf39906a596ea41f=1708583696; SoundValue=0.50; sdidtest=0UnHUgv0_qmfD4KAKlwzhqQB32nywGZJYLZl_9RLv0Lbi5CGYYNiBGLrvNZVszz4FEo_unffNsxk9BdvXKO_PkvC5cOwCJ13goOiNYGClLirWVkn9LtfFJw_Qo4kgKr8OZHDqNnuwg612sGyflFn1draukOt03gk2m3pwGbiKsB143MJhMxcI458jIjiX0MYq; sdidshorttest=test; __yasmid=0.8936157401010706; _yasids=__rootsid^%^3DCAA3838C53600001F4EE863017406250; huyawap_rep_cnt=4; udb_passdata=3; huya_web_rep_cnt=89; huya_flash_rep_cnt=20; Hm_lpvt_51700b6c722f5bb4cf39906a596ea41f=1709548534; _rep_cnt=3; PHPSESSID=r0klm0vccf08q1das65bnd8co1; guid=0a7df378828609654d01a205a305fb52; huya_hd_rep_cnt=8',
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    json_str = re.findall('stream: (\\{"data".*?),"iWebDefaultBitRate"', html_str)[0]
    json_data = json.loads(json_str + '}')
    return json_data


@trace_error_decorator
async def get_huya_app_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'ios/7.830 (ios 17.0; ; iPhone 15 (A2846/A3089/A3090/A3092))',
        'xweb_xhr': '1',
        'referer': 'https://servicewechat.com/wx74767bf0b684f7d3/301/page-frame.html',
        'accept-language': 'zh-CN,zh;q=0.9',
    }

    if cookies:
        headers['Cookie'] = cookies
    room_id = url.split('?')[0].rsplit('/', maxsplit=1)[-1]

    if any(char.isalpha() for char in room_id):
        html_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
        room_id = re.search('ProfileRoom":(.*?),"sPrivateHost', html_str)
        if room_id:
            room_id = room_id.group(1)
        else:
            raise Exception('Please use "https://www.huya.com/+room_number" for recording')

    params = {
        'm': 'Live',
        'do': 'profileRoom',
        'roomid': room_id,
        'showSecret': '1',
    }
    wx_app_api = f'https://mp.huya.com/cache.php?{urllib.parse.urlencode(params)}'
    json_str = await async_req(url=wx_app_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)
    anchor_name = json_data['data']['profileInfo']['nick']
    live_status = json_data['data']['realLiveStatus']
    live_title = json_data['data']['liveData']['introduction']
    if live_status != 'ON':
        return {'anchor_name': anchor_name, 'is_live': False}
    else:
        base_steam_info_list = json_data['data']['stream']['baseSteamInfoList']
        play_url_list = []
        for i in base_steam_info_list:
            cdn_type = i['sCdnType']
            stream_name = i['sStreamName']
            s_flv_url = i['sFlvUrl']
            flv_anti_code = i['sFlvAntiCode']
            s_hls_url = i['sHlsUrl']
            hls_anti_code = i['sHlsAntiCode']
            m3u8_url = f'{s_hls_url}/{stream_name}.m3u8?{hls_anti_code}'
            flv_url = f'{s_flv_url}/{stream_name}.flv?{flv_anti_code}'
            play_url_list.append(
                {
                    'cdn_type': cdn_type,
                    'm3u8_url': m3u8_url,
                    'flv_url': flv_url,
                }
            )
        #print(json.dumps(play_url_list, indent=4, ensure_ascii=False))
        # flv_url = 'https://' + play_url_list[0]['flv_url'].split('://')[1]
        # record_url = flv_url

        # 设定优先级，优先选择 TX,2025/03/14时AL不可用
        priority_order = ["TX", "HW", "HS", "AL"]

        # 查找优先的 flv_url
        selected_flv_url = None
        selected_cdn_type = None

        for cdn in priority_order:
            for item in play_url_list:
                if item["cdn_type"] == cdn:
                    selected_flv_url = item["flv_url"]
                    selected_cdn_type = cdn
                    break
            if selected_flv_url:
                break

        # 处理 flv_url，确保使用 https
        if selected_flv_url:
            flv_url = 'https://' + selected_flv_url.split('://')[1]

            # 如果选择的是 TX，执行额外的字符串替换
            if selected_cdn_type == "TX":
                flv_url = flv_url.replace("&ctype=tars_mp", "&ctype=huya_webh5").replace("&fs=bhct", "&fs=bgct")

            record_url = flv_url
        else:
            record_url = None

        return {
            'anchor_name': anchor_name,
            'is_live': True,
            'm3u8_url': play_url_list[0]['m3u8_url'],
            'flv_url': play_url_list[0]['flv_url'],
            'record_url': record_url,
            'title': live_title
        }
