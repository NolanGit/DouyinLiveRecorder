# -*- encoding: utf-8 -*-
"""Platform handler registry.

Each entry maps a URL substring → ``handler(record_url, record_quality,
monitor_proxy_address)`` returning ``(platform_name, port_info, new_record_url)``.

Handlers are split between :mod:`platform_handlers_cn` and
:mod:`platform_handlers_os` to keep modules <300 LOC. The registry exposes a
``HANDLERS`` list whose order matches the original elif chain in the legacy
``main.py`` so that disambiguation between overlapping URL substrings is
preserved.
"""
from __future__ import annotations

from typing import Callable

from . import platform_handlers_cn as cn
from . import platform_handlers_os as os_

Handler = Callable[[str, str, str | None], tuple[str, dict, str]]

# (url_substring, handler) — order is significant.
HANDLERS: list[tuple[str | tuple[str, ...], Handler]] = [
    ("douyin.com/", cn.handle_douyin),
    ("https://www.tiktok.com/", os_.handle_tiktok),
    ("https://live.kuaishou.com/", cn.handle_kuaishou),
    ("https://www.huya.com/", cn.handle_huya),
    ("https://www.douyu.com/", cn.handle_douyu),
    ("https://www.yy.com/", cn.handle_yy),
    ("https://live.bilibili.com/", cn.handle_bilibili),
    (("http://xhslink.com/", "https://www.xiaohongshu.com/"), cn.handle_xiaohongshu),
    (("www.bigo.tv/", "slink.bigovideo.tv/"), cn.handle_bigo),
    ("https://app.blued.cn/", cn.handle_blued),
    (("sooplive.co.kr/", "sooplive.com/"), os_.handle_sooplive),
    ("cc.163.com/", cn.handle_netease),
    ("qiandurebo.com/", cn.handle_qiandurebo),
    ("www.pandalive.co.kr/", os_.handle_pandatv),
    ("fm.missevan.com/", cn.handle_maoerfm),
    ("www.winktv.co.kr/", os_.handle_winktv),
    (("www.flextv.co.kr/", "www.ttinglive.com/"), os_.handle_flextv),
    ("look.163.com/", cn.handle_look),
    ("www.popkontv.com/", os_.handle_popkontv),
    ("twitcasting.tv/", os_.handle_twitcasting),
    ("live.baidu.com/", cn.handle_baidu),
    ("weibo.com/", cn.handle_weibo),
    ("kugou.com/", cn.handle_kugou),
    ("www.twitch.tv/", os_.handle_twitch),
    ("www.liveme.com/", os_.handle_liveme),
    ("www.huajiao.com/", cn.handle_huajiao),
    ("7u66.com/", cn.handle_liuxing),
    ("showroom-live.com/", os_.handle_showroom),
    (("live.acfun.cn/", "m.acfun.cn/"), cn.handle_acfun),
    ("live.tlclw.com/", cn.handle_changliao),
    ("ybw1666.com/", cn.handle_yinbo),
    ("www.inke.cn/", cn.handle_yingke),
    ("www.zhihu.com/", cn.handle_zhihu),
    ("chzzk.naver.com/", os_.handle_chzzk),
    ("www.haixiutv.com/", cn.handle_haixiu),
    ("vvxqiu.com/", cn.handle_vvxqiu),
    ("17.live/", cn.handle_17live),
    ("www.lang.live/", cn.handle_langlive),
    ("m.pp.weimipopo.com/", cn.handle_pplive),
    (".6.cn/", cn.handle_six_room),
    ("lehaitv.com/", cn.handle_lehaitv),
    ("h.catshow168.com/", cn.handle_huamao),
    (("live.shopee", "shp.ee/"), os_.handle_shopee),
    (("www.youtube.com/", "youtu.be/"), os_.handle_youtube),
    ("tb.cn", cn.handle_taobao),
    (("3.cn", "m.jd.com"), cn.handle_jd),
    ("faceit.com/", os_.handle_faceit),
    (("www.miguvideo.com", "m.miguvideo.com"), cn.handle_migu),
    ("show.lailianjie.com", cn.handle_lianjie),
    ("www.imkktv.com", cn.handle_laixiu),
    ("www.picarto.tv", os_.handle_picarto),
]


def find_handler(record_url: str) -> Handler | None:
    """Return the first matching handler for ``record_url`` or ``None``."""
    for keys, handler in HANDLERS:
        if isinstance(keys, str):
            if keys in record_url:
                return handler
        else:
            if any(k in record_url for k in keys):
                return handler
    return None
