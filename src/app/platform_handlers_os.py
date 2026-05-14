# -*- encoding: utf-8 -*-
"""Overseas platform handlers.

Most overseas streamers require a proxy: when one is not available the
function logs an error and returns empty ``port_info`` so the recorder thread
can retry on the next loop.
"""
from __future__ import annotations

import asyncio

from src import spider, stream, utils
from src.utils import logger

from . import state


def _need_proxy(monitor_proxy_address: str | None) -> bool:
    return bool(state.global_proxy or monitor_proxy_address)


def handle_tiktok(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_tiktok_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.tiktok_cookie))
            port_info = asyncio.run(
                stream.get_tiktok_stream_url(json_data, record_quality, monitor_proxy_address))
        else:
            logger.error("错误信息: 网络异常，请检查网络是否能正常访问TikTok平台")
            port_info = []
    return 'TikTok直播', port_info, ''


def handle_sooplive(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_sooplive_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.sooplive_cookie,
                username=state.sooplive_username, password=state.sooplive_password))
            if json_data and json_data.get('new_cookies'):
                utils.update_config(
                    state.config_file, 'Cookie', 'sooplive_cookie',
                    json_data['new_cookies'])
            port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问SOOP平台")
            port_info = []
    return 'SOOP', port_info, ''


def handle_pandatv(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_pandatv_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.pandatv_cookie))
            port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问PandaTV直播平台")
            port_info = []
    return 'PandaTV', port_info, ''


def handle_winktv(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_winktv_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.winktv_cookie))
            port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问WinkTV直播平台")
            port_info = []
    return 'WinkTV', port_info, ''


def handle_flextv(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_flextv_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.flextv_cookie,
                username=state.flextv_username, password=state.flextv_password))
            if json_data and json_data.get('new_cookies'):
                utils.update_config(
                    state.config_file, 'Cookie', 'flextv_cookie',
                    json_data['new_cookies'])
            if 'play_url_list' in json_data:
                port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
            else:
                port_info = json_data
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问FlexTV直播平台")
            port_info = []
    return 'FlexTV', port_info, ''


def handle_popkontv(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            port_info = asyncio.run(spider.get_popkontv_stream_url(
                url=record_url, proxy_addr=monitor_proxy_address,
                access_token=state.popkontv_access_token,
                username=state.popkontv_username, password=state.popkontv_password,
                partner_code=state.popkontv_partner_code))
            if port_info and port_info.get('new_token'):
                utils.update_config(
                    file_path=state.config_file, section='Authorization',
                    key='popkontv_token', new_value=port_info['new_token'])
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问PopkonTV直播平台")
            port_info = []
    return 'PopkonTV', port_info, ''


def handle_twitcasting(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_twitcasting_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address,
            cookies=state.twitcasting_cookie,
            account_type=state.twitcasting_account_type,
            username=state.twitcasting_username, password=state.twitcasting_password))
        port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=False))
        if port_info and port_info.get('new_cookies'):
            utils.update_config(
                file_path=state.config_file, section='Cookie',
                key='twitcasting_cookie', new_value=port_info['new_cookies'])
    return 'TwitCasting', port_info, ''


def handle_twitch(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_twitchtv_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.twitch_cookie))
            port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问TwitchTV直播平台")
            port_info = []
    return 'TwitchTV', port_info, ''


def handle_liveme(record_url, record_quality, monitor_proxy_address):
    if _need_proxy(monitor_proxy_address):
        with state.semaphore:
            port_info = asyncio.run(spider.get_liveme_stream_url(
                url=record_url, proxy_addr=monitor_proxy_address, cookies=state.liveme_cookie))
        return 'LiveMe', port_info, ''
    logger.error("错误信息: 网络异常，请检查本网络是否能正常访问LiveMe直播平台")
    return '未知平台', [], ''


def handle_showroom(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_showroom_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.showroom_cookie))
        port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
    return 'ShowRoom', port_info, ''


def handle_chzzk(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_chzzk_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.chzzk_cookie))
        port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
    return 'CHZZK', port_info, ''


def handle_shopee(record_url, record_quality, monitor_proxy_address):
    new_record_url = ''
    with state.semaphore:
        port_info = asyncio.run(spider.get_shopee_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.shopee_cookie))
        if port_info.get('uid'):
            new_record_url = record_url.split('?')[0] + '?' + str(port_info['uid'])
    return 'shopee', port_info, new_record_url


def handle_youtube(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_youtube_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.youtube_cookie))
        port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
    return 'Youtube', port_info, ''


def handle_faceit(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if _need_proxy(monitor_proxy_address):
            json_data = asyncio.run(spider.get_faceit_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address,
                cookies=state.faceit_cookie))
            port_info = asyncio.run(stream.get_stream_url(json_data, record_quality, spec=True))
        else:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问faceit直播平台")
            port_info = []
    return 'faceit', port_info, ''


def handle_picarto(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_picarto_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.picarto_cookie))
    return 'Picarto', port_info, ''
