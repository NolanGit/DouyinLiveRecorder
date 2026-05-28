# -*- encoding: utf-8 -*-

import json
import re

from .base import OptionalStr, async_req, trace_error_decorator


@trace_error_decorator
async def get_qiandurebo_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://qiandurebo.com/web/index.php',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    if cookies:
        headers['Cookie'] = cookies

    html_str = await async_req(url=url, proxy_addr=proxy_addr, headers=headers)
    data = re.search('var user = (.*?)\r\n\\s+user\\.play_url', html_str, re.DOTALL).group(1)
    anchor_name = re.findall('"zb_nickname": "(.*?)",\r\n', data)

    result = {"anchor_name": "", "is_live": False}
    if len(anchor_name) > 0:
        result['anchor_name'] = anchor_name[0]
        play_url = re.findall('"play_url": "(.*?)",\r\n', data)

        if len(play_url) > 0 and 'common-text-center" style="display:block' not in html_str:
            result |= {
                'anchor_name': anchor_name[0],
                'is_live': True,
                'flv_url': play_url[0],
                'record_url': play_url[0]
            }
    return result
