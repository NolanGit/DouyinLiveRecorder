# -*- encoding: utf-8 -*-

"""
Shared imports, constants and utility functions used by all platform spiders.
"""

import ssl
import re
import urllib.parse
from typing import List

from ..utils import trace_error_decorator, generate_random_string
from ..http_clients.async_http import async_req
from ..room import get_sec_user_id, get_unique_id, UnsupportedUrlError
from ..ab_sign import ab_sign
from .. import JS_SCRIPT_PATH, utils
from ..logger import script_path

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

OptionalStr = str | None
OptionalDict = dict | None


def get_params(url: str, params: str) -> OptionalStr:
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    if params in query_params:
        return query_params[params][0]


async def get_play_url_list(m3u8: str, proxy: OptionalStr = None, header: OptionalDict = None,
                            abroad: bool = False) -> List[str]:
    resp = await async_req(url=m3u8, proxy_addr=proxy, headers=header, abroad=abroad)
    play_url_list = []
    for i in resp.split('\n'):
        if i.startswith('https://'):
            play_url_list.append(i.strip())
    if not play_url_list:
        for i in resp.split('\n'):
            if i.strip().endswith('m3u8'):
                play_url_list.append(i.strip())
    bandwidth_pattern = re.compile(r'BANDWIDTH=(\d+)')
    bandwidth_list = bandwidth_pattern.findall(resp)
    url_to_bandwidth = {url: int(bandwidth) for bandwidth, url in zip(bandwidth_list, play_url_list)}
    play_url_list = sorted(play_url_list, key=lambda url: url_to_bandwidth[url], reverse=True)
    return play_url_list
