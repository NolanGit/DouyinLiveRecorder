# -*- encoding: utf-8 -*-

import json
import re
import urllib.parse
import uuid
from typing import List

from .base import OptionalStr, get_params, async_req, trace_error_decorator


def _loads_soop(json_str: str, api_name: str) -> dict:
    """Parse a SOOP API response defensively.

    ``async_req`` 在网络异常时会吞掉异常并返回错误字符串而非 JSON，
    SOOP 接口也偶发返回空响应。直接 ``json.loads`` 会抛出难以理解的
    "Expecting value: line 1 column 1 (char 0)"。这里转成带接口名和响应
    片段的清晰错误，便于定位是哪个接口的瞬时空响应（recorder 下一轮会重试）。
    """
    if not json_str or not json_str.strip():
        raise RuntimeError(f"SOOP {api_name} 返回空响应（可能是网络瞬时错误或被限流），将重试")
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        snippet = json_str.strip()[:120]
        raise RuntimeError(
            f"SOOP {api_name} 返回非 JSON 响应（可能是网络瞬时错误或被限流），将重试。响应片段: {snippet!r}"
        ) from e


def _get_soop_data(json_data: dict, api_name: str) -> dict:
    data = json_data.get("data") if isinstance(json_data, dict) else None
    if isinstance(data, dict):
        return data

    snippet = json.dumps(json_data, ensure_ascii=False)[:200]
    raise RuntimeError(
        f"SOOP {api_name} 响应缺少 data 字段（可能是接口限流、鉴权失效或平台返回异常），将重试。响应片段: {snippet!r}"
    )


@trace_error_decorator
async def login_sooplive(username: str, password: str, proxy_addr: OptionalStr = None) -> OptionalStr:
    if len(username) < 6 or len(password) < 10:
        raise RuntimeError("sooplive login failed! Please enter the correct account and password for the sooplive "
                           "platform in the config.ini file.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://play.sooplive.co.kr',
        'Referer': 'https://play.sooplive.co.kr/superbsw123/277837074',
    }

    data = {
        'szWork': 'login',
        'szType': 'json',
        'szUid': username,
        'szPassword': password,
        'isSaveId': 'true',
        'isSavePw': 'true',
        'isSaveJoin': 'true',
        'isLoginRetain': 'Y',
    }

    url = 'https://login.sooplive.co.kr/app/LoginAction.php'

    try:
        cookie_dict = await async_req(url, proxy_addr=proxy_addr, headers=headers,
                                      data=data, return_cookies=True, timeout=20)
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
        return cookie_str
    except Exception as e:
        print(f"An error occurred during login: {e}")
        raise Exception(
            "sooplive login failed, please check if the account password in the configuration file is correct."
        )


@trace_error_decorator
async def get_sooplive_cdn_url(broad_no: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Origin': 'https://play.sooplive.co.kr',
        'Referer': 'https://play.sooplive.co.kr/oul282/249469582',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    if cookies:
        headers['Cookie'] = cookies

    params = {
        'return_type': 'gcp_cdn',
        'use_cors': 'false',
        'cors_origin_url': 'play.sooplive.co.kr',
        'broad_key': f'{broad_no}-common-master-hls',
        'time': '8361.086329376785',
    }

    query = urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for host in ("livestream-manager.sooplive.com", "livestream-manager.sooplive.co.kr"):
        url2 = f'http://{host}/broad_stream_assign.html?{query}'
        json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, abroad=True)
        try:
            return _loads_soop(json_str, f"broad_stream_assign({host})")
        except RuntimeError as e:
            last_error = e

    raise last_error or RuntimeError("SOOP broad_stream_assign failed")


@trace_error_decorator
async def get_sooplive_tk(url: str, rtype: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> str | tuple:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Origin': 'https://play.sooplive.co.kr',
        'Referer': 'https://play.sooplive.co.kr/secretx/250989857',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    if cookies:
        headers['Cookie'] = cookies

    split_url = url.split('/')
    bj_id = split_url[3] if len(split_url) < 6 else split_url[5]
    room_password = get_params(url, "pwd")
    if not room_password:
        room_password = ''
    data = {
        'bid': bj_id,
        'bno': '',
        'type': rtype,
        'pwd': room_password,
        'player_type': 'html5',
        'stream_type': 'common',
        'quality': 'master',
        'mode': 'landing',
        'from_api': '0',
        'is_revive': 'false',
    }

    url2 = f'https://live.sooplive.co.kr/afreeca/player_live_api.php?bjid={bj_id}'
    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = _loads_soop(json_str, "player_live_api")

    if rtype == 'aid':
        token = json_data["CHANNEL"]["AID"]
        return token
    else:
        bj_name = json_data['CHANNEL']['BJNICK']
        bj_id = json_data['CHANNEL']['BJID']
        return f"{bj_name}-{bj_id}", json_data['CHANNEL']['BNO']


def get_soop_headers(cookies):
    headers = {
        'client-id': str(uuid.uuid4()),
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, '
                      'like Gecko) Version/18.5 Mobile/15E148 Safari/604.1 Edg/141.0.0.0',
    }
    if cookies:
        headers['cookie'] = cookies
    return headers


async def _get_soop_channel_info_global(bj_id, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> str:
    headers = get_soop_headers(cookies)
    api = 'https://api.sooplive.com/v2/channel/info/' + str(bj_id)
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = _loads_soop(json_str, "channel/info")
    nickname = json_data['data']['streamerChannelInfo']['nickname']
    channelId = json_data['data']['streamerChannelInfo']['channelId']
    anchor_name = f"{nickname}-{channelId}"
    return anchor_name


async def _get_soop_stream_info_global(bj_id, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    headers = get_soop_headers(cookies)
    api = 'https://api.sooplive.com/v2/stream/info/' + str(bj_id)
    json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
    json_data = _loads_soop(json_str, "stream/info")
    status = json_data['data']['isStream']
    title = json_data['data']['title']
    return status, title


async def _fetch_web_stream_data_global(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    split_url = url.split('/')
    bj_id = split_url[3] if len(split_url) < 6 else split_url[5]
    anchor_name = await _get_soop_channel_info_global(bj_id)
    result = {"anchor_name": anchor_name or '', "is_live": False, "live_url": url}
    status, title = await _get_soop_stream_info_global(bj_id)
    if not status:
        return result
    else:
        async def _get_url_list(m3u8: str) -> list[str]:
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
            }
            if cookies:
                headers['cookie'] = cookies
            resp = await async_req(url=m3u8, proxy_addr=proxy_addr, headers=headers)
            play_url_list = []
            url_prefix = '/'.join(m3u8.split('/')[0:3])
            for i in resp.split('\n'):
                if not i.startswith('#') and i.strip():
                    play_url_list.append(url_prefix + i.strip())
            bandwidth_pattern = re.compile(r'BANDWIDTH=(\d+)')
            bandwidth_list = bandwidth_pattern.findall(resp)
            url_to_bandwidth = {purl: int(bandwidth) for bandwidth, purl in zip(bandwidth_list, play_url_list)}
            play_url_list = sorted(play_url_list, key=lambda purl: url_to_bandwidth[purl], reverse=True)
            return play_url_list

        m3u8_url = 'https://global-media.sooplive.com/live/' + str(bj_id) + '/master.m3u8'
        result |= {
            'is_live': True,
            'title': title,
            'm3u8_url': m3u8_url,
            'play_url_list': await _get_url_list(m3u8_url)
        }
    return result


@trace_error_decorator
async def get_sooplive_stream_data(
        url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None,
        username: OptionalStr = None, password: OptionalStr = None
) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://m.sooplive.co.kr/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    if cookies:
        headers['Cookie'] = cookies

    # 仅 www.sooplive.com（国际版主页/频道页）走 global API；
    # play.sooplive.com/<bjid>/<broadno> 实际是韩版直播间，应走 co.kr API。
    if "www.sooplive.com" in url:
        return await _fetch_web_stream_data_global(url, proxy_addr, cookies)

    split_url = url.split('/')
    bj_id = split_url[3] if len(split_url) < 6 else split_url[5]

    data = {
        'bj_id': bj_id,
        'broad_no': '',
        'agent': 'web',
        'confirm_adult': 'true',
        'player_type': 'webm',
        'mode': 'live',
    }

    url2 = 'http://api.m.sooplive.co.kr/broad/a/watch'

    json_str = await async_req(url=url2, proxy_addr=proxy_addr, headers=headers, data=data, abroad=True)
    json_data = _loads_soop(json_str, "broad/a/watch")
    watch_data = _get_soop_data(json_data, "broad/a/watch")

    if 'user_nick' in watch_data:
        anchor_name = watch_data['user_nick']
        if "bj_id" in watch_data:
            anchor_name = f"{anchor_name}-{watch_data['bj_id']}"
    else:
        anchor_name = ''

    result = {"anchor_name": anchor_name or '' ,"is_live": False}

    async def get_url_list(m3u8: str) -> List[str]:
        resp = await async_req(url=m3u8, proxy_addr=proxy_addr, headers=headers, abroad=True)
        play_url_list = []
        url_prefix = m3u8.rsplit('/', maxsplit=1)[0] + '/'
        for i in resp.split('\n'):
            if i.startswith('auth_playlist'):
                play_url_list.append(url_prefix + i.strip())
        bandwidth_pattern = re.compile(r'BANDWIDTH=(\d+)')
        bandwidth_list = bandwidth_pattern.findall(resp)
        url_to_bandwidth = {purl: int(bandwidth) for bandwidth, purl in zip(bandwidth_list, play_url_list)}
        play_url_list = sorted(play_url_list, key=lambda purl: url_to_bandwidth[purl], reverse=True)
        return play_url_list

    if not anchor_name:
        async def handle_login() -> OptionalStr:
            cookie = await login_sooplive(username, password, proxy_addr=proxy_addr)
            if 'AuthTicket=' in cookie:
                print("sooplive platform login successful! Starting to fetch live streaming data...")
                return cookie

        async def fetch_data(cookie, _result) -> dict:
            aid_token = await get_sooplive_tk(url, rtype='aid', proxy_addr=proxy_addr, cookies=cookie)
            _anchor_name, _broad_no = await get_sooplive_tk(url, rtype='info', proxy_addr=proxy_addr, cookies=cookie)
            _view_url_data = await get_sooplive_cdn_url(_broad_no, proxy_addr=proxy_addr)
            _view_url = _view_url_data['view_url']
            _m3u8_url = _view_url + '?aid=' + aid_token
            _result |= {
                "anchor_name": _anchor_name,
                "is_live": True,
                "m3u8_url": _m3u8_url,
                'play_url_list': await get_url_list(_m3u8_url),
                'new_cookies': cookie
            }
            return _result

        if watch_data.get('code') == -3001:
            print("sooplive live stream failed to retrieve, the live stream just ended.")
            return result

        elif watch_data.get('code') == -3002:
            print("sooplive live stream retrieval failed, the live needs 19+, you are not logged in.")
            print("Attempting to log in to the sooplive live streaming platform with your account and password, "
                  "please ensure it is configured.")
            new_cookie = await handle_login()
            if new_cookie and len(new_cookie) > 0:
                return await fetch_data(new_cookie, result)
            raise RuntimeError("sooplive login failed, please check if the account and password are correct")

        elif watch_data.get('code') == -3004:
            if cookies and len(cookies) > 0:
                return await fetch_data(cookies, result)
            else:
                raise RuntimeError("sooplive login failed, please check if the account and password are correct")
        elif watch_data.get('code') == -6001:
            print("error message：Please check if the input sooplive live room address "
                  "is correct.")
            return result
    if json_data.get('result') == 1 and anchor_name:
        broad_no = watch_data.get('broad_no')
        if not broad_no:
            raise RuntimeError("SOOP broad/a/watch 响应缺少 broad_no 字段，将重试")
        # 注意：移动端 ``api.m.sooplive.co.kr/broad/a/watch`` 返回的 ``hls_authentication_key``
        # 是受限的移动端 token，对应的 ``master.m3u8`` 只会返回 hd(540p) 一档清晰度。
        # 必须改用桌面端 ``player_live_api.php`` 取 aid token，才能在同一个
        # ``auth_master_playlist.m3u8`` 上拿到完整的 original(1080p)/hd4k/hd/sd 多档清晰度。
        try:
            aid_token = await get_sooplive_tk(url, rtype='aid', proxy_addr=proxy_addr, cookies=cookies)
        except Exception:  # noqa: BLE001
            # 桌面端 API 失败时降级回移动端 token，至少能拿到 540p 录制。
            aid_token = watch_data.get('hls_authentication_key')
            if not aid_token:
                raise RuntimeError("SOOP broad/a/watch 响应缺少 hls_authentication_key 字段，将重试")
        view_url_data = await get_sooplive_cdn_url(broad_no, proxy_addr=proxy_addr)
        view_url = view_url_data['view_url']
        m3u8_url = view_url + '?aid=' + aid_token
        result |= {'is_live': True, 'm3u8_url': m3u8_url, 'play_url_list': await get_url_list(m3u8_url)}
    result['new_cookies'] = None
    return result
