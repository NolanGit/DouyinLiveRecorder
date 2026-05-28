# -*- encoding: utf-8 -*-

import json
import random
import urllib.parse

from .base import OptionalStr, async_req, trace_error_decorator, generate_random_string, get_play_url_list


async def get_twitchtv_room_info(url: str, token: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> tuple:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept-Language': 'zh-CN',
        'Referer': 'https://www.twitch.tv/',
        'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'Client-Integrity': token,
        'Content-Type': 'text/plain;charset=UTF-8',
    }
    if cookies:
        headers['Cookie'] = cookies
    uid = url.split('?')[0].rsplit('/', maxsplit=1)[-1]

    data = [
        {
            "operationName": "ChannelShell",
            "variables": {
                "login": uid
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "580ab410bcd0c1ad194224957ae2241e5d252b2c5173d8e0cce9d32d5bb14efe"
                }
            }
        },
    ]

    json_str = await async_req('https://gql.twitch.tv/gql', proxy_addr=proxy_addr, headers=headers,
                               json_data=data, abroad=True)
    json_data = json.loads(json_str)
    user_data = json_data[0]['data']['userOrError']
    login_name = user_data["login"]
    nickname = f"{user_data['displayName']}-{login_name}"
    status = True if user_data['stream'] else False
    return nickname, status


@trace_error_decorator
async def get_twitchtv_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'en-US',
        'Referer': 'https://www.twitch.tv/',
        'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'device-id': generate_random_string(16).lower(),
    }

    if cookies:
        headers['Cookie'] = cookies
    uid = url.split('?')[0].rsplit('/', maxsplit=1)[-1]

    data = {
        "operationName": "PlaybackAccessToken_Template",
        "query": "query PlaybackAccessToken_Template($login: String!, $isLive: Boolean!, $vodID: ID!, "
                 "$isVod: Boolean!, $playerType: String!) {  streamPlaybackAccessToken(channelName: $login, "
                 "params: {platform: \"web\", playerBackend: \"mediaplayer\", playerType: $playerType}) @include(if: "
                 "$isLive) {    value    signature   authorization { isForbidden forbiddenReasonCode }   __typename  "
                 "}  videoPlaybackAccessToken(id: $vodID, params: {platform: \"web\", playerBackend: \"mediaplayer\", "
                 "playerType: $playerType}) @include(if: $isVod) {    value    signature   __typename  }}",
        "variables": {
            "isLive": True,
            "login": uid,
            "isVod": False,
            "vodID": "",
            "playerType": "site"
        }
    }

    json_str = await async_req('https://gql.twitch.tv/gql', proxy_addr=proxy_addr, headers=headers,
                               json_data=data, abroad=True)
    json_data = json.loads(json_str)
    token = json_data['data']['streamPlaybackAccessToken']['value']
    sign = json_data['data']['streamPlaybackAccessToken']['signature']

    anchor_name, live_status = await get_twitchtv_room_info(url=url, token=token, proxy_addr=proxy_addr, cookies=cookies)
    result = {"anchor_name": anchor_name, "is_live": live_status}
    if live_status:
        play_session_id = random.choice(["bdd22331a986c7f1073628f2fc5b19da", "064bc3ff1722b6f53b0b5b8c01e46ca5"])
        params = {
            "acmb": "e30=",
            "allow_source": "true",
            "browser_family": "firefox",
            "browser_version": "124.0",
            "cdm": "wv",
            "fast_bread": "true",
            "os_name": "Windows",
            "os_version": "NT%2010.0",
            "p": "3553732",
            "platform": "web",
            "play_session_id": play_session_id,
            "player_backend": "mediaplayer",
            "player_version": "1.28.0-rc.1",
            "playlist_include_framerate": "true",
            "reassignments_supported": "true",
            "sig": sign,
            "token": token,
            "transcode_mode": "cbr_v1"
        }
        access_key = urllib.parse.urlencode(params)
        m3u8_url = f'https://usher.ttvnw.net/api/channel/hls/{uid}.m3u8?{access_key}'
        play_url_list = await get_play_url_list(m3u8=m3u8_url, proxy=proxy_addr, header=headers, abroad=True)
        result |= {'m3u8_url': m3u8_url, 'play_url_list': play_url_list}
    return result
