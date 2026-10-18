# -*- coding: utf-8 -*-
import asyncio
import threading

import httpx
from typing import Dict, Any
from .. import utils

OptionalStr = str | None
OptionalDict = Dict[str, Any] | None

# 每个录制线程复用自己的连接池。监控轮询间隔只有几十到上百秒，
# 每次新建 Client 都会重新握手。
_clients = threading.local()


def _client_key(proxy: OptionalStr, verify: bool, http2: bool) -> tuple:
    return (proxy, bool(verify), bool(http2))


async def _get_client(proxy: OptionalStr, verify: bool, http2: bool) -> httpx.AsyncClient:
    """按代理 / TLS 校验 / HTTP2 复用当前线程、当前 event loop 上的 AsyncClient。"""
    cache: dict = getattr(_clients, "cache", None)
    if cache is None:
        cache = {}
        _clients.cache = cache
    key = _client_key(proxy, verify, http2)
    loop_id = id(asyncio.get_running_loop())
    cached = cache.get(key)
    if cached is not None:
        client, bound_loop = cached
        if bound_loop == loop_id and not client.is_closed:
            return client
        if not client.is_closed:
            await client.aclose()
    client = httpx.AsyncClient(proxy=proxy, verify=verify, http2=http2)
    cache[key] = (client, loop_id)
    return client


async def async_req(
        url: str,
        proxy_addr: OptionalStr = None,
        headers: OptionalDict = None,
        data: dict | bytes | None = None,
        json_data: dict | list | None = None,
        timeout: int = 20,
        redirect_url: bool = False,
        return_cookies: bool = False,
        include_cookies: bool = False,
        abroad: bool = False,
        content_conding: str = 'utf-8',
        verify: bool = False,
        http2: bool = True
) -> OptionalDict | OptionalStr | tuple:
    if headers is None:
        headers = {}
    try:
        proxy_addr = utils.handle_proxy_addr(proxy_addr)
        client = await _get_client(proxy_addr, verify, http2)
        if data or json_data:
            response = await client.post(
                url, data=data, json=json_data, headers=headers, timeout=timeout,
            )
        else:
            response = await client.get(
                url, headers=headers, follow_redirects=True, timeout=timeout,
            )

        if redirect_url:
            return str(response.url)
        elif return_cookies:
            cookies_dict = {name: value for name, value in response.cookies.items()}
            return (response.text, cookies_dict) if include_cookies else cookies_dict
        else:
            resp_str = response.text
    except Exception as e:
        resp_str = str(e)

    return resp_str


async def get_response_status(url: str, proxy_addr: OptionalStr = None, headers: OptionalDict = None,
                              timeout: int = 10, abroad: bool = False, verify: bool = False, http2=False) -> bool:

    try:
        proxy_addr = utils.handle_proxy_addr(proxy_addr)
        client = await _get_client(proxy_addr, verify, http2)
        response = await client.head(
            url, headers=headers, follow_redirects=True, timeout=timeout,
        )
        return response.status_code == 200
    except Exception as e:
        print(e)
    return False
