# -*- encoding: utf-8 -*-

import hashlib
import json
import re
import time
import uuid

from .base import OptionalStr, trace_error_decorator, async_req


@trace_error_decorator
async def get_laixiu_stream_url(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    def generate_uuid(ua_type: str):
        if ua_type == "mobile":
            return str(uuid.uuid4())
        return str(uuid.uuid4()).replace('-', '')

    def calculate_sign(ua_type: str = 'pc'):
        a = int(time.time() * 1000)
        s = generate_uuid(ua_type)
        u = 'kk792f28d6ff1f34ec702c08626d454b39pro'

        input_str = f"web{s}{a}{u}"
        md5_hash = hashlib.md5(input_str.encode('utf-8')).hexdigest()

        return {
            'timestamp': a,
            'imei': s,
            'requestId': md5_hash,
            'inputString': input_str
        }

    sign_data = calculate_sign(ua_type='pc')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'mobileModel': 'web',
        'timestamp': str(sign_data['timestamp']),
        'loginType': '2',
        'versionCode': '10003',
        'imei': sign_data['imei'],
        'requestId': sign_data['requestId'],
        'channel': '9',
        'version': '1.0.0',
        'os': 'web',
        'platform': 'WEB',
        'Origin': 'https://www.imkktv.com',
        'Referer': 'https://www.imkktv.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    }

    if cookies:
        headers['cookie'] = cookies

    pattern = r"(?:roomId|anchorId)=(.*?)(?=&|$)"
    match = re.search(pattern, url)
    room_id = match.group(1) if match else ''
    play_api = f'https://api.imkktv.com/liveroom/getShareLiveVideo?roomId={room_id}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_data = json.loads(json_str)

    room_data = json_data['data']
    anchor_name = room_data['nickname']
    live_status = room_data['playStatus'] == 0

    result = {"anchor_name": anchor_name, "is_live": False}
    if live_status:
        flv_url = room_data['playUrl']
        result |= {'is_live': True, 'flv_url': flv_url, 'record_url': flv_url}
    return result
