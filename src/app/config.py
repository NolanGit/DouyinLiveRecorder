# -*- encoding: utf-8 -*-
"""Configuration loading helpers.

Reads ``config/config.ini`` and assigns every value into :mod:`src.app.state`,
keeping the original public API of the legacy ``main.py`` unchanged.
"""
from __future__ import annotations

import builtins
import configparser
import threading
import urllib.request
from typing import Any
from urllib.error import HTTPError, URLError

from src.proxy import ProxyDetector

from . import state


def read_config_value(config_parser: configparser.RawConfigParser,
                      section: str, option: str, default_value: Any) -> Any:
    """Read an INI value, creating section/option with the default if missing."""
    try:
        config_parser.read(state.config_file, encoding=state.text_encoding)
        for sec in ('录制设置', '推送配置', 'Cookie', 'Authorization', '账号密码'):
            if sec not in config_parser.sections():
                config_parser.add_section(sec)
        return config_parser.get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        config_parser.set(section, option, str(default_value))
        with open(state.config_file, 'w', encoding=state.text_encoding) as f:
            config_parser.write(f)
        return default_value


def detect_global_proxy() -> None:
    """Probe for a system proxy and update ``state.global_proxy`` accordingly."""
    try:
        if state.skip_proxy_check:
            state.global_proxy = True
            return
        print('系统代理检测中，请耐心等待...')
        urllib.request.urlopen("https://www.google.com/", timeout=15)
        state.global_proxy = True
        print('\r全局/规则网络代理已开启√')
        pd = ProxyDetector()
        if pd.is_proxy_enabled():
            proxy_info = pd.get_proxy_info()
            print(f"System Proxy: http://{proxy_info.ip}:{proxy_info.port}")
    except HTTPError as err:
        print(f"HTTP error occurred: {err.code} - {err.reason}")
    except URLError:
        state.color_obj.print_colored(
            "INFO：未检测到全局/规则网络代理，请检查代理配置（若无需录制海外直播请忽略此条提示）",
            state.color_obj.YELLOW,
        )
    except Exception as err:  # noqa: BLE001
        print("An unexpected error occurred:", err)


def init_language() -> None:
    """Read the ``language`` switch and patch ``builtins.print`` for i18n."""
    config = configparser.RawConfigParser()
    state.language = read_config_value(config, '录制设置', 'language(zh_cn/en)', "zh_cn")
    state.skip_proxy_check = state.options.get(
        read_config_value(config, '录制设置', '是否跳过代理检测(是/否)', "否"), False,
    )
    if state.language and 'en' not in state.language.lower():
        from i18n import translated_print
        builtins.print = translated_print


def load(config: configparser.RawConfigParser | None = None) -> configparser.RawConfigParser:
    """Read every configuration value into :mod:`src.app.state`."""
    if config is None:
        config = configparser.RawConfigParser()

    rc = lambda section, option, default: read_config_value(config, section, option, default)  # noqa: E731
    opts = state.options.get

    state.video_save_path = rc('录制设置', '直播保存路径(不填则默认)', "")
    state.folder_by_author = opts(rc('录制设置', '保存文件夹是否以作者区分', "是"), False)
    state.folder_by_time = opts(rc('录制设置', '保存文件夹是否以时间区分', "否"), False)
    state.folder_by_title = opts(rc('录制设置', '保存文件夹是否以标题区分', "否"), False)
    state.filename_by_title = opts(rc('录制设置', '保存文件名是否包含标题', "否"), False)
    state.clean_emoji = opts(rc('录制设置', '是否去除名称中的表情符号', "是"), True)
    state.video_save_type = rc('录制设置', '视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频', "ts")
    state.video_record_quality = rc('录制设置', '原画|超清|高清|标清|流畅', "原画")
    state.use_proxy = opts(rc('录制设置', '是否使用代理ip(是/否)', "是"), False)
    state.use_proxy_for_monitoring = opts(rc('录制设置', '是否使用代理监控直播状态(是/否)', "是"), True)
    state.use_proxy_for_recording = opts(rc('录制设置', '是否使用代理录制直播流(是/否)', "是"), True)
    state.proxy_addr_bak = rc('录制设置', '代理地址', "")
    state.proxy_addr = None if not state.use_proxy else state.proxy_addr_bak
    state.max_request = int(rc('录制设置', '同一时间访问网络的线程数', 3))
    state.semaphore = threading.Semaphore(state.max_request)
    state.delay_default = int(rc('录制设置', '循环时间(秒)', 120))
    state.local_delay_default = int(rc('录制设置', '排队读取网址时间(秒)', 0))
    state.loop_time = opts(rc('录制设置', '是否显示循环秒数', "否"), False)
    state.show_url = opts(rc('录制设置', '是否显示直播源地址', "否"), False)
    state.split_video_by_time = opts(rc('录制设置', '分段录制是否开启', "否"), False)
    state.enable_https_recording = opts(rc('录制设置', '是否强制启用https录制', "否"), False)
    state.disk_space_limit = float(rc('录制设置', '录制空间剩余阈值(gb)', 1.0))
    state.split_time = str(rc('录制设置', '视频分段时间(秒)', 1800))
    state.converts_to_mp4 = opts(rc('录制设置', '录制完成后自动转为mp4格式', "否"), False)
    state.converts_to_h264 = opts(rc('录制设置', 'mp4格式重新编码为h264', "否"), False)
    state.delete_origin_file = opts(rc('录制设置', '追加格式后删除原文件', "否"), False)
    state.create_time_file = opts(rc('录制设置', '生成时间字幕文件', "否"), False)
    state.is_run_script = opts(rc('录制设置', '是否录制完成后执行自定义脚本', "否"), False)
    state.custom_script = rc('录制设置', '自定义脚本执行命令', "") if state.is_run_script else None
    state.enable_proxy_platform = rc(
        '录制设置', '使用代理录制的平台(逗号分隔)',
        'tiktok, soop, pandalive, winktv, flextv, popkontv, twitch, liveme, '
        'showroom, chzzk, shopee, shp, youtu, faceit',
    )
    state.enable_proxy_platform_list = (
        state.enable_proxy_platform.replace('，', ',').split(',')
        if state.enable_proxy_platform else None
    )
    state.extra_enable_proxy = rc('录制设置', '额外使用代理录制的平台(逗号分隔)', '')
    state.extra_enable_proxy_platform_list = (
        state.extra_enable_proxy.replace('，', ',').split(',')
        if state.extra_enable_proxy else None
    )

    state.live_status_push = rc('推送配置', '直播状态推送渠道', "")
    state.dingtalk_api_url = rc('推送配置', '钉钉推送接口链接', "")
    state.xizhi_api_url = rc('推送配置', '微信推送接口链接', "")
    state.bark_msg_api = rc('推送配置', 'bark推送接口链接', "")
    state.bark_msg_level = rc('推送配置', 'bark推送中断级别', "active")
    state.bark_msg_ring = rc('推送配置', 'bark推送铃声', "bell")
    state.dingtalk_phone_num = rc('推送配置', '钉钉通知@对象(填手机号)', "")
    state.dingtalk_is_atall = opts(rc('推送配置', '钉钉通知@全体(是/否)', "否"), False)
    state.tg_token = rc('推送配置', 'tgapi令牌', "")
    state.tg_chat_id = rc('推送配置', 'tg聊天id(个人或者群组id)', "")
    state.email_host = rc('推送配置', 'SMTP邮件服务器', "")
    state.open_smtp_ssl = opts(rc('推送配置', '是否使用SMTP服务SSL加密(是/否)', "是"), True)
    state.smtp_port = rc('推送配置', 'SMTP邮件服务器端口', "")
    state.login_email = rc('推送配置', '邮箱登录账号', "")
    state.email_password = rc('推送配置', '发件人密码(授权码)', "")
    state.sender_email = rc('推送配置', '发件人邮箱', "")
    state.sender_name = rc('推送配置', '发件人显示昵称', "")
    state.to_email = rc('推送配置', '收件人邮箱', "")
    state.ntfy_api = rc('推送配置', 'ntfy推送地址', "")
    state.ntfy_tags = rc('推送配置', 'ntfy推送标签', "tada")
    state.ntfy_email = rc('推送配置', 'ntfy推送邮箱', "")
    state.pushplus_token = rc('推送配置', 'pushplus推送token', "")
    state.push_message_title = rc('推送配置', '自定义推送标题', "直播间状态更新通知")
    state.begin_push_message_text = rc('推送配置', '自定义开播推送内容', "")
    state.over_push_message_text = rc('推送配置', '自定义关播推送内容', "")
    state.disable_record = opts(rc('推送配置', '只推送通知不录制(是/否)', "否"), False)
    state.push_check_seconds = int(rc('推送配置', '直播推送检测频率(秒)', 1800))
    state.begin_show_push = opts(rc('推送配置', '开播推送开启(是/否)', "是"), True)
    state.over_show_push = opts(rc('推送配置', '关播推送开启(是/否)', "否"), False)

    # ---- 监控时间窗口 ----
    state.time_window_enabled = opts(rc('录制设置', '监控时间窗口开启(是/否)', "否"), False)
    state.time_window_start = rc('录制设置', '监控开始时间(时分)', "00:00")
    state.time_window_end = rc('录制设置', '监控结束时间(时分)', "23:59")
    state.time_window_cycle = rc('录制设置', '监控重复周期(每天/每周/每月/自定义)', "每天")
    _weekdays_str = rc('录制设置', '监控生效星期(1-7逗号分隔)', "1,2,3,4,5,6,7")
    _monthdays_str = rc('录制设置', '监控生效日期(1-31逗号分隔)',
                        "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31")
    from .time_window import parse_int_list, validate_config, TimeWindowConfig
    state.time_window_weekdays = parse_int_list(_weekdays_str, 1, 7)
    state.time_window_monthdays = parse_int_list(_monthdays_str, 1, 31)

    if state.time_window_enabled:
        _tw_cfg = TimeWindowConfig(
            enabled=True,
            start_time=state.time_window_start,
            end_time=state.time_window_end,
            repeat_cycle=state.time_window_cycle,
            weekdays=state.time_window_weekdays,
            monthdays=state.time_window_monthdays,
        )
        _valid, _err = validate_config(_tw_cfg)
        if not _valid:
            from src.utils import logger
            logger.warning(f"监控时间窗口配置无效，已禁用: {_err}")
            state.time_window_enabled = False

    state.sooplive_username = rc('账号密码', 'sooplive账号', '')
    state.sooplive_password = rc('账号密码', 'sooplive密码', '')
    state.flextv_username = rc('账号密码', 'flextv账号', '')
    state.flextv_password = rc('账号密码', 'flextv密码', '')
    state.popkontv_username = rc('账号密码', 'popkontv账号', '')
    state.popkontv_partner_code = rc('账号密码', 'partner_code', 'P-00001')
    state.popkontv_password = rc('账号密码', 'popkontv密码', '')
    state.twitcasting_account_type = rc('账号密码', 'twitcasting账号类型', 'normal')
    state.twitcasting_username = rc('账号密码', 'twitcasting账号', '')
    state.twitcasting_password = rc('账号密码', 'twitcasting密码', '')
    state.popkontv_access_token = rc('Authorization', 'popkontv_token', '')

    cookie_keys = [
        ('dy_cookie', '抖音cookie'), ('ks_cookie', '快手cookie'),
        ('tiktok_cookie', 'tiktok_cookie'), ('hy_cookie', '虎牙cookie'),
        ('douyu_cookie', '斗鱼cookie'), ('yy_cookie', 'yy_cookie'),
        ('bili_cookie', 'B站cookie'), ('xhs_cookie', '小红书cookie'),
        ('bigo_cookie', 'bigo_cookie'), ('blued_cookie', 'blued_cookie'),
        ('sooplive_cookie', 'sooplive_cookie'), ('netease_cookie', 'netease_cookie'),
        ('qiandurebo_cookie', '千度热播_cookie'), ('pandatv_cookie', 'pandatv_cookie'),
        ('maoerfm_cookie', '猫耳fm_cookie'), ('winktv_cookie', 'winktv_cookie'),
        ('flextv_cookie', 'flextv_cookie'), ('look_cookie', 'look_cookie'),
        ('twitcasting_cookie', 'twitcasting_cookie'), ('baidu_cookie', 'baidu_cookie'),
        ('weibo_cookie', 'weibo_cookie'), ('kugou_cookie', 'kugou_cookie'),
        ('twitch_cookie', 'twitch_cookie'), ('liveme_cookie', 'liveme_cookie'),
        ('huajiao_cookie', 'huajiao_cookie'), ('liuxing_cookie', 'liuxing_cookie'),
        ('showroom_cookie', 'showroom_cookie'), ('acfun_cookie', 'acfun_cookie'),
        ('changliao_cookie', 'changliao_cookie'), ('yinbo_cookie', 'yinbo_cookie'),
        ('yingke_cookie', 'yingke_cookie'), ('zhihu_cookie', 'zhihu_cookie'),
        ('chzzk_cookie', 'chzzk_cookie'), ('haixiu_cookie', 'haixiu_cookie'),
        ('vvxqiu_cookie', 'vvxqiu_cookie'), ('yiqilive_cookie', '17live_cookie'),
        ('langlive_cookie', 'langlive_cookie'), ('pplive_cookie', 'pplive_cookie'),
        ('six_room_cookie', '6room_cookie'), ('lehaitv_cookie', 'lehaitv_cookie'),
        ('huamao_cookie', 'huamao_cookie'), ('shopee_cookie', 'shopee_cookie'),
        ('youtube_cookie', 'youtube_cookie'), ('taobao_cookie', 'taobao_cookie'),
        ('jd_cookie', 'jd_cookie'), ('faceit_cookie', 'faceit_cookie'),
        ('migu_cookie', 'migu_cookie'), ('lianjie_cookie', 'lianjie_cookie'),
        ('laixiu_cookie', 'laixiu_cookie'), ('picarto_cookie', 'picarto_cookie'),
    ]
    for attr, ini_key in cookie_keys:
        setattr(state, attr, rc('Cookie', ini_key, ''))

    if state.video_save_type and state.video_save_type.upper() in state.VIDEO_SAVE_TYPE_LIST:
        state.video_save_type = state.video_save_type.upper()
    else:
        state.video_save_type = "TS"

    return config
