# -*- encoding: utf-8 -*-
"""Domestic platform handlers (China-region streamers).

Each handler returns ``(platform, port_info, new_record_url)`` where
``new_record_url`` is normally ``''`` and ``port_info`` is the dict shape
produced by :mod:`src.stream`.
"""
from __future__ import annotations

import asyncio

from src import spider, stream

from . import state


def handle_douyin(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if 'v.douyin.com' not in record_url and '/user/' not in record_url:
            json_data = asyncio.run(spider.get_douyin_web_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address, cookies=state.dy_cookie))
        else:
            json_data = asyncio.run(spider.get_douyin_app_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address, cookies=state.dy_cookie))
        port_info = asyncio.run(
            stream.get_douyin_stream_url(json_data, record_quality, monitor_proxy_address))
    return '抖音直播', port_info, ''


def handle_kuaishou(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_kuaishou_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.ks_cookie))
        port_info = asyncio.run(stream.get_kuaishou_stream_url(json_data, record_quality))
    return '快手直播', port_info, ''


def handle_huya(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        if record_quality not in ['OD', 'BD', 'UHD']:
            json_data = asyncio.run(spider.get_huya_stream_data(
                url=record_url, proxy_addr=monitor_proxy_address, cookies=state.hy_cookie))
            port_info = asyncio.run(stream.get_huya_stream_url(json_data, record_quality))
        else:
            port_info = asyncio.run(spider.get_huya_app_stream_url(
                url=record_url, proxy_addr=monitor_proxy_address, cookies=state.hy_cookie))
    return '虎牙直播', port_info, ''


def handle_douyu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_douyu_info_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.douyu_cookie))
        port_info = asyncio.run(stream.get_douyu_stream_url(
            json_data, video_quality=record_quality, cookies=state.douyu_cookie,
            proxy_addr=monitor_proxy_address))
    return '斗鱼直播', port_info, ''


def handle_yy(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_yy_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.yy_cookie))
        port_info = asyncio.run(stream.get_yy_stream_url(json_data))
    return 'YY直播', port_info, ''


def handle_bilibili(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_bilibili_room_info(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.bili_cookie))
        port_info = asyncio.run(stream.get_bilibili_stream_url(
            json_data, video_quality=record_quality, cookies=state.bili_cookie,
            proxy_addr=monitor_proxy_address))
    return 'B站直播', port_info, ''


def handle_xiaohongshu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_xhs_stream_url(
            record_url, proxy_addr=monitor_proxy_address, cookies=state.xhs_cookie))
    return '小红书直播', port_info, ''


def handle_bigo(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_bigo_stream_url(
            record_url, proxy_addr=monitor_proxy_address, cookies=state.bigo_cookie))
    return 'Bigo直播', port_info, ''


def handle_blued(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_blued_stream_url(
            record_url, proxy_addr=monitor_proxy_address, cookies=state.blued_cookie))
    return 'Blued直播', port_info, ''


def handle_netease(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_netease_stream_data(
            url=record_url, cookies=state.netease_cookie))
        port_info = asyncio.run(stream.get_netease_stream_url(json_data, record_quality))
    return '网易CC直播', port_info, ''


def handle_qiandurebo(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_qiandurebo_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.qiandurebo_cookie))
    return '千度热播', port_info, ''


def handle_maoerfm(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_maoerfm_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.maoerfm_cookie))
    return '猫耳FM直播', port_info, ''


def handle_look(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_looklive_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.look_cookie))
    return 'Look直播', port_info, ''


def handle_baidu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_baidu_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.baidu_cookie))
        port_info = asyncio.run(stream.get_stream_url(json_data, record_quality))
    return '百度直播', port_info, ''


def handle_weibo(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_weibo_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.weibo_cookie))
        port_info = asyncio.run(stream.get_stream_url(
            json_data, record_quality, hls_extra_key='m3u8_url'))
    return '微博直播', port_info, ''


def handle_kugou(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_kugou_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.kugou_cookie))
    return '酷狗直播', port_info, ''


def handle_huajiao(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_huajiao_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.huajiao_cookie))
    return '花椒直播', port_info, ''


def handle_liuxing(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_liuxing_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.liuxing_cookie))
    return '流星直播', port_info, ''


def handle_acfun(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_acfun_stream_data(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.acfun_cookie))
        port_info = asyncio.run(stream.get_stream_url(
            json_data, record_quality, url_type='flv', flv_extra_key='url'))
    return 'Acfun', port_info, ''


def handle_changliao(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_changliao_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.changliao_cookie))
    return '畅聊直播', port_info, ''


def handle_yinbo(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_yinbo_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.yinbo_cookie))
    return '音播直播', port_info, ''


def handle_yingke(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_yingke_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.yingke_cookie))
    return '映客直播', port_info, ''


def handle_zhihu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_zhihu_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.zhihu_cookie))
    return '知乎直播', port_info, ''


def handle_haixiu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_haixiu_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.haixiu_cookie))
    return '嗨秀直播', port_info, ''


def handle_vvxqiu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_vvxqiu_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.vvxqiu_cookie))
    return 'VV星球', port_info, ''


def handle_17live(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_17live_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.yiqilive_cookie))
    return '17Live', port_info, ''


def handle_langlive(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_langlive_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.langlive_cookie))
    return '浪Live', port_info, ''


def handle_pplive(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_pplive_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.pplive_cookie))
    return '漂漂直播', port_info, ''


def handle_six_room(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_6room_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.six_room_cookie))
    return '六间房直播', port_info, ''


def handle_lehaitv(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_haixiu_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.lehaitv_cookie))
    return '乐嗨直播', port_info, ''


def handle_huamao(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_pplive_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.huamao_cookie))
    return '花猫直播', port_info, ''


def handle_taobao(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        json_data = asyncio.run(spider.get_taobao_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.taobao_cookie))
        port_info = asyncio.run(stream.get_stream_url(
            json_data, record_quality, url_type='all',
            hls_extra_key='hlsUrl', flv_extra_key='flvUrl'))
    return '淘宝直播', port_info, ''


def handle_jd(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_jd_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.jd_cookie))
    return '京东直播', port_info, ''


def handle_migu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_migu_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.migu_cookie))
    return '咪咕直播', port_info, ''


def handle_lianjie(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_lianjie_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.lianjie_cookie))
    return '连接直播', port_info, ''


def handle_laixiu(record_url, record_quality, monitor_proxy_address):
    with state.semaphore:
        port_info = asyncio.run(spider.get_laixiu_stream_url(
            url=record_url, proxy_addr=monitor_proxy_address, cookies=state.laixiu_cookie))
    return '来秀直播', port_info, ''
