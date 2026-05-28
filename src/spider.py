# -*- encoding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Date: 2023-07-15 23:15:00
Update: 2025-10-23 18:28:00
Copyright (c) 2023-2025 by Hmily, All Rights Reserved.
Function: Get live stream data.

This module re-exports all platform spider functions from the
src.spiders sub-package for backward compatibility.
"""

__all__ = [
    # common utilities
    "ssl_context", "OptionalStr", "OptionalDict", "get_params", "get_play_url_list",
    # douyin
    "get_douyin_web_stream_data", "get_douyin_app_stream_data", "get_douyin_stream_data",
    # tiktok
    "get_tiktok_stream_data",
    # kuaishou
    "get_kuaishou_stream_data", "get_kuaishou_stream_data2",
    # huya
    "get_huya_stream_data", "get_huya_app_stream_url",
    # douyu
    "md5", "get_token_js", "get_douyu_info_data", "get_douyu_stream_data",
    # yy
    "get_yy_stream_data",
    # bilibili
    "get_bilibili_room_info_h5", "get_bilibili_room_info", "get_bilibili_stream_data",
    # xhs / bigo / blued
    "get_xhs_stream_url", "get_bigo_stream_url", "get_blued_stream_url",
    # soop
    "login_sooplive", "get_sooplive_cdn_url", "get_sooplive_tk",
    "get_soop_headers", "get_sooplive_stream_data",
    # netease / qiandurebo / pandatv / maoerfm
    "get_netease_stream_data", "get_qiandurebo_stream_data",
    "get_pandatv_stream_data", "get_maoerfm_stream_url",
    # winktv / flextv
    "get_winktv_bj_info", "get_winktv_stream_data",
    "login_flextv", "get_flextv_stream_url", "get_flextv_stream_data",
    # look / popkontv / twitcasting
    "get_looklive_secret_data", "get_looklive_stream_url",
    "login_popkontv", "get_popkontv_stream_data", "get_popkontv_stream_url",
    "login_twitcasting", "get_twitcasting_stream_url",
    # baidu / weibo / kugou
    "get_baidu_stream_data", "get_weibo_stream_data", "get_kugou_stream_url",
    # twitch / liveme
    "get_twitchtv_room_info", "get_twitchtv_stream_data", "get_liveme_stream_url",
    # huajiao
    "get_huajiao_sn", "get_huajiao_user_info",
    "get_huajiao_stream_url_app", "get_huajiao_stream_url",
    # liuxing / showroom / acfun / changliao
    "get_liuxing_stream_url", "get_showroom_stream_data",
    "get_acfun_sign_params", "get_acfun_stream_data", "get_changliao_stream_url",
    # yingke / yinbo / zhihu / chzzk
    "get_yingke_stream_url", "get_yinbo_stream_url",
    "get_zhihu_stream_url", "get_chzzk_stream_data",
    # haixiu / vvxqiu / 17live / langlive / pplive
    "get_haixiu_stream_url", "get_vvxqiu_stream_url", "get_17live_stream_url",
    "get_langlive_stream_url", "get_pplive_stream_url",
    # six_room / shopee / youtube / taobao / jd
    "get_6room_stream_url", "get_shopee_stream_url", "get_youtube_stream_url",
    "get_taobao_stream_url", "get_jd_stream_url",
    # faceit / migu / lianjie / laixiu / picarto
    "get_faceit_stream_data", "get_migu_stream_url",
    "get_lianjie_stream_url", "get_laixiu_stream_url", "get_picarto_stream_url",
]

# ── common utilities ──────────────────────────────────────────────
from .spiders.base import (
    ssl_context, OptionalStr, OptionalDict,
    get_params, get_play_url_list,
)

# ── platform spiders ─────────────────────────────────────────────
from .spiders.douyin_spider import (
    get_douyin_web_stream_data, get_douyin_app_stream_data, get_douyin_stream_data,
)
from .spiders.tiktok_spider import get_tiktok_stream_data
from .spiders.kuaishou_spider import get_kuaishou_stream_data, get_kuaishou_stream_data2
from .spiders.huya_spider import get_huya_stream_data, get_huya_app_stream_url
from .spiders.douyu_spider import md5, get_token_js, get_douyu_info_data, get_douyu_stream_data
from .spiders.yy_spider import get_yy_stream_data
from .spiders.bilibili_spider import (
    get_bilibili_room_info_h5, get_bilibili_room_info, get_bilibili_stream_data,
)
from .spiders.xhs_spider import get_xhs_stream_url
from .spiders.bigo_spider import get_bigo_stream_url
from .spiders.blued_spider import get_blued_stream_url
from .spiders.soop_spider import (
    login_sooplive, get_sooplive_cdn_url, get_sooplive_tk,
    get_soop_headers, get_sooplive_stream_data,
)
from .spiders.netease_spider import get_netease_stream_data
from .spiders.qiandurebo_spider import get_qiandurebo_stream_data
from .spiders.pandatv_spider import get_pandatv_stream_data
from .spiders.maoerfm_spider import get_maoerfm_stream_url
from .spiders.winktv_spider import get_winktv_bj_info, get_winktv_stream_data
from .spiders.flextv_spider import login_flextv, get_flextv_stream_url, get_flextv_stream_data
from .spiders.look_spider import get_looklive_secret_data, get_looklive_stream_url
from .spiders.popkontv_spider import (
    login_popkontv, get_popkontv_stream_data, get_popkontv_stream_url,
)
from .spiders.twitcasting_spider import login_twitcasting, get_twitcasting_stream_url
from .spiders.baidu_spider import get_baidu_stream_data
from .spiders.weibo_spider import get_weibo_stream_data
from .spiders.kugou_spider import get_kugou_stream_url
from .spiders.twitch_spider import get_twitchtv_room_info, get_twitchtv_stream_data
from .spiders.liveme_spider import get_liveme_stream_url
from .spiders.huajiao_spider import (
    get_huajiao_sn, get_huajiao_user_info,
    get_huajiao_stream_url_app, get_huajiao_stream_url,
)
from .spiders.liuxing_spider import get_liuxing_stream_url
from .spiders.showroom_spider import get_showroom_stream_data
from .spiders.acfun_spider import get_acfun_sign_params, get_acfun_stream_data
from .spiders.changliao_spider import get_changliao_stream_url
from .spiders.yingke_spider import get_yingke_stream_url
from .spiders.yinbo_spider import get_yinbo_stream_url
from .spiders.zhihu_spider import get_zhihu_stream_url
from .spiders.chzzk_spider import get_chzzk_stream_data
from .spiders.haixiu_spider import get_haixiu_stream_url
from .spiders.vvxqiu_spider import get_vvxqiu_stream_url
from .spiders.live17_spider import get_17live_stream_url
from .spiders.langlive_spider import get_langlive_stream_url
from .spiders.pplive_spider import get_pplive_stream_url
from .spiders.six_room_spider import get_6room_stream_url
from .spiders.shopee_spider import get_shopee_stream_url
from .spiders.youtube_spider import get_youtube_stream_url
from .spiders.taobao_spider import get_taobao_stream_url
from .spiders.jd_spider import get_jd_stream_url
from .spiders.faceit_spider import get_faceit_stream_data
from .spiders.migu_spider import get_migu_stream_url
from .spiders.lianjie_spider import get_lianjie_stream_url
from .spiders.laixiu_spider import get_laixiu_stream_url
from .spiders.picarto_spider import get_picarto_stream_url
