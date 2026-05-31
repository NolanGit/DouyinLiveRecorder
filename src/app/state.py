# -*- encoding: utf-8 -*-
"""Shared mutable state and module-wide constants.

All modules in :mod:`src.app` import attributes from this module instead of
re-declaring globals. Mutating shared state should be done as
``state.<name> = value`` rather than re-binding via ``from state import x``.
"""
from __future__ import annotations

import datetime
import os
import sys
import threading
from typing import Any

from src import utils

# ---------- runtime metadata (immutable) ----------
version = "v4.0.7"
platforms = (
    "\n国内站点：抖音|快手|虎牙|斗鱼|YY|B站|小红书|bigo|blued|网易CC|千度热播|猫耳FM|Look|TwitCasting|百度|微博|"
    "酷狗|花椒|流星|Acfun|畅聊|映客|音播|知乎|嗨秀|VV星球|17Live|浪Live|漂漂|六间房|乐嗨|花猫|淘宝|京东|咪咕|连接|来秀"
    "\n海外站点：TikTok|SOOP|PandaTV|WinkTV|FlexTV|PopkonTV|TwitchTV|LiveMe|ShowRoom|CHZZK|Shopee|"
    "Youtube|Faceit|Picarto"
)

script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
config_file = f"{script_path}/config/config.ini"
url_config_file = f"{script_path}/config/URL_config.ini"
backup_dir = f"{script_path}/backup_config"
text_encoding = "utf-8-sig"
rstr = r"[\/\\\:\*\？?\"\<\>\|&#.。,， ~！· ]"
default_path = f"{script_path}/downloads"
os_type = os.name
clear_command = "cls" if os_type == "nt" else "clear"
color_obj = utils.Color()

# ---------- mutable runtime state ----------
recording: set = set()
error_count: int = 0
pre_max_request: int = 10
max_request_lock = threading.Lock()
file_update_lock = threading.Lock()
error_window: list = []
error_window_size: int = 10
error_threshold: int = 5
monitoring: int = 0
running_list: set = set()  # 已启动录制线程的 URL 集合（O(1) 查找）
url_tuples_list: set = set()  # 待启动的 (quality, url, name) 三元组集合
url_comments: list = []
text_no_repeat_url: list = []
create_var: dict = {}
first_start: bool = True
exit_recording: bool = False
need_update_line_list: list = []
first_run: bool = True
not_record_list: list = []
start_display_time = datetime.datetime.now()
global_proxy: bool = False
recording_time_list: dict = {}
ini_URL_content: str = ""

# ---- url_loader 解析缓存 ----
url_config_mtime: float = 0.0  # 上次解析时 URL_config.ini 的 mtime
url_config_size: int = -1      # 上次解析时 URL_config.ini 的 size，结合 mtime 判断变化
url_config_parse_lock = threading.Lock()

options: dict = {"是": True, "否": False}

# ---------- runtime configuration values (populated by config.load()) ----------
language: str = "zh_cn"
skip_proxy_check: bool = False
video_save_path: str = ""
folder_by_author: bool = True
folder_by_time: bool = False
folder_by_title: bool = False
filename_by_title: bool = False
clean_emoji: bool = True
video_save_type: str = "TS"
video_record_quality: str = "原画"
use_proxy: bool = False
use_proxy_for_monitoring: bool = True
use_proxy_for_recording: bool = True
proxy_addr_bak: str = ""
proxy_addr: str | None = None
max_request: int = 3
semaphore: threading.Semaphore = threading.Semaphore(3)
delay_default: int = 120
local_delay_default: int = 0
loop_time: bool = False
show_url: bool = False
split_video_by_time: bool = False
enable_https_recording: bool = False
disk_space_limit: float = 1.0
split_time: str = "1800"
converts_to_mp4: bool = False
converts_to_h264: bool = False
delete_origin_file: bool = False
create_time_file: bool = False
is_run_script: bool = False
custom_script: str | None = None
enable_proxy_platform: str = ""
enable_proxy_platform_list: list | None = None
extra_enable_proxy: str = ""
extra_enable_proxy_platform_list: list | None = None
live_status_push: str = ""
dingtalk_api_url: str = ""
xizhi_api_url: str = ""
bark_msg_api: str = ""
bark_msg_level: str = "active"
bark_msg_ring: str = "bell"
dingtalk_phone_num: str = ""
dingtalk_is_atall: bool = False
tg_token: str = ""
tg_chat_id: str = ""
email_host: str = ""
open_smtp_ssl: bool = True
smtp_port: str = ""
login_email: str = ""
email_password: str = ""
sender_email: str = ""
sender_name: str = ""
to_email: str = ""
ntfy_api: str = ""
ntfy_tags: str = "tada"
ntfy_email: str = ""
pushplus_token: str = ""
push_message_title: str = "直播间状态更新通知"
begin_push_message_text: str = ""
over_push_message_text: str = ""
disable_record: bool = False
push_check_seconds: int = 1800
begin_show_push: bool = True
over_show_push: bool = False

# ---- monitoring time window ----
time_window_enabled: bool = False
time_window_start: str = "00:00"
time_window_end: str = "23:59"
time_window_cycle: str = "每天"
time_window_weekdays: list[int] = [1, 2, 3, 4, 5, 6, 7]
time_window_monthdays: list[int] = list(range(1, 32))

# ---- account credentials ----
sooplive_username: str = ""
sooplive_password: str = ""
flextv_username: str = ""
flextv_password: str = ""
popkontv_username: str = ""
popkontv_partner_code: str = "P-00001"
popkontv_password: str = ""
twitcasting_account_type: str = "normal"
twitcasting_username: str = ""
twitcasting_password: str = ""
popkontv_access_token: str = ""

# ---- per-platform cookies ----
dy_cookie: str = ""
ks_cookie: str = ""
tiktok_cookie: str = ""
hy_cookie: str = ""
douyu_cookie: str = ""
yy_cookie: str = ""
bili_cookie: str = ""
xhs_cookie: str = ""
bigo_cookie: str = ""
blued_cookie: str = ""
sooplive_cookie: str = ""
netease_cookie: str = ""
qiandurebo_cookie: str = ""
pandatv_cookie: str = ""
maoerfm_cookie: str = ""
winktv_cookie: str = ""
flextv_cookie: str = ""
look_cookie: str = ""
twitcasting_cookie: str = ""
baidu_cookie: str = ""
weibo_cookie: str = ""
kugou_cookie: str = ""
twitch_cookie: str = ""
liveme_cookie: str = ""
huajiao_cookie: str = ""
liuxing_cookie: str = ""
showroom_cookie: str = ""
acfun_cookie: str = ""
changliao_cookie: str = ""
yinbo_cookie: str = ""
yingke_cookie: str = ""
zhihu_cookie: str = ""
chzzk_cookie: str = ""
haixiu_cookie: str = ""
vvxqiu_cookie: str = ""
yiqilive_cookie: str = ""
langlive_cookie: str = ""
pplive_cookie: str = ""
six_room_cookie: str = ""
lehaitv_cookie: str = ""
huamao_cookie: str = ""
shopee_cookie: str = ""
youtube_cookie: str = ""
taobao_cookie: str = ""
jd_cookie: str = ""
faceit_cookie: str = ""
migu_cookie: str = ""
lianjie_cookie: str = ""
laixiu_cookie: str = ""
picarto_cookie: str = ""

# ---------- platform host catalogues (used by url_loader & recorder) ----------
PLATFORM_HOST = [
    'live.douyin.com', 'v.douyin.com', 'www.douyin.com', 'live.kuaishou.com',
    'www.huya.com', 'www.douyu.com', 'www.yy.com', 'live.bilibili.com',
    'www.redelight.cn', 'www.xiaohongshu.com', 'xhslink.com', 'www.bigo.tv',
    'slink.bigovideo.tv', 'app.blued.cn', 'cc.163.com', 'qiandurebo.com',
    'fm.missevan.com', 'look.163.com', 'twitcasting.tv', 'live.baidu.com',
    'weibo.com', 'fanxing.kugou.com', 'fanxing2.kugou.com', 'mfanxing.kugou.com',
    'www.huajiao.com', 'www.7u66.com', 'wap.7u66.com', 'live.acfun.cn',
    'm.acfun.cn', 'live.tlclw.com', 'wap.tlclw.com', 'live.ybw1666.com',
    'wap.ybw1666.com', 'www.inke.cn', 'www.zhihu.com', 'www.haixiutv.com',
    'h5webcdnp.vvxqiu.com', '17.live', 'www.lang.live', 'm.pp.weimipopo.com',
    'v.6.cn', 'm.6.cn', 'www.lehaitv.com', 'h.catshow168.com', 'e.tb.cn',
    'huodong.m.taobao.com', '3.cn', 'eco.m.jd.com', 'www.miguvideo.com',
    'm.miguvideo.com', 'show.lailianjie.com', 'www.imkktv.com', 'www.picarto.tv',
]

OVERSEAS_PLATFORM_HOST = [
    'www.tiktok.com', 'play.sooplive.co.kr', 'm.sooplive.co.kr',
    'www.sooplive.com', 'm.sooplive.com', 'play.sooplive.com', 'www.pandalive.co.kr',
    'www.winktv.co.kr', 'www.flextv.co.kr', 'www.ttinglive.com',
    'www.popkontv.com', 'www.twitch.tv', 'www.liveme.com',
    'www.showroom-live.com', 'chzzk.naver.com', 'm.chzzk.naver.com',
    'live.shopee.', '.shp.ee', 'www.youtube.com', 'youtu.be', 'www.faceit.com',
]

ALL_PLATFORM_HOST = PLATFORM_HOST + OVERSEAS_PLATFORM_HOST

CLEAN_URL_HOST_LIST = (
    'live.douyin.com', 'live.bilibili.com', 'www.huajiao.com', 'www.zhihu.com',
    'www.huya.com', 'chzzk.naver.com', 'www.liveme.com', 'www.haixiutv.com',
    'v.6.cn', 'm.6.cn', 'www.lehaitv.com',
)

VIDEO_SAVE_TYPE_LIST = ("FLV", "MKV", "TS", "MP4", "MP3音频", "M4A音频", "MP3", "M4A")
QUALITY_CHOICES = ("原画", "蓝光", "超清", "高清", "标清", "流畅")


def ensure_runtime_dirs() -> None:
    """Create directories that the application expects to exist."""
    os.makedirs(default_path, exist_ok=True)


def get(name: str, default: Any = None) -> Any:
    """Generic accessor used by tests and helpers that prefer a callable API."""
    return globals().get(name, default)
