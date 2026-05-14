# -*- encoding: utf-8 -*-
"""Multi-channel push-message dispatcher."""
from __future__ import annotations

from msg_push import (
    bark, dingtalk, ntfy, pushplus, send_email, tg_bot, xizhi,
)

from . import state


def push_message(record_name: str, live_url: str, content: str) -> None:
    """Dispatch ``content`` to every channel enabled in ``live_status_push``."""
    msg_title = (state.push_message_title or '').strip() or "直播间状态更新通知"
    push_functions = {
        '微信': lambda: xizhi(state.xizhi_api_url, msg_title, content),
        '钉钉': lambda: dingtalk(
            state.dingtalk_api_url, content,
            state.dingtalk_phone_num, state.dingtalk_is_atall,
        ),
        '邮箱': lambda: send_email(
            state.email_host, state.login_email, state.email_password,
            state.sender_email, state.sender_name, state.to_email,
            msg_title, content, state.smtp_port, state.open_smtp_ssl,
        ),
        'TG': lambda: tg_bot(state.tg_chat_id, state.tg_token, content),
        'BARK': lambda: bark(
            state.bark_msg_api, title=msg_title, content=content,
            level=state.bark_msg_level, sound=state.bark_msg_ring,
        ),
        'NTFY': lambda: ntfy(
            state.ntfy_api, title=msg_title, content=content,
            tags=state.ntfy_tags, action_url=live_url, email=state.ntfy_email,
        ),
        'PUSHPLUS': lambda: pushplus(state.pushplus_token, msg_title, content),
    }

    for platform, func in push_functions.items():
        if platform in (state.live_status_push or '').upper():
            try:
                result = func()
                print(
                    f'提示信息：已经将[{record_name}]直播状态消息推送至你的{platform},'
                    f' 成功{len(result["success"])}, 失败{len(result["error"])}'
                )
            except Exception as e:  # noqa: BLE001 - propagate-friendly logging
                state.color_obj.print_colored(
                    f"直播消息推送到{platform}失败: {e}", state.color_obj.RED,
                )
