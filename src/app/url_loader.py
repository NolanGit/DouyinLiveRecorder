# -*- encoding: utf-8 -*-
"""URL_config.ini parsing & validation.

Reads each line of ``URL_config.ini``, normalises it (deduplication, comment
handling, host whitelisting), and emits ``(quality, url, name)`` tuples that
the recorder thread can consume.
"""
from __future__ import annotations

import os
import re

from src.utils import logger

from . import state
from .file_ops import delete_line, update_file
from .naming import contains_url


def ensure_url_config_ready() -> None:
    """Make sure ``config.ini`` and ``URL_config.ini`` exist and have content."""
    try:
        if not os.path.isfile(state.config_file):
            with open(state.config_file, 'w', encoding=state.text_encoding):
                pass

        ini_url_content = ''
        if os.path.isfile(state.url_config_file):
            with open(state.url_config_file, 'r', encoding=state.text_encoding) as f:
                ini_url_content = f.read().strip()
        state.ini_URL_content = ini_url_content

        if not ini_url_content.strip():
            input_url = input('请输入要录制的主播直播间网址（尽量使用PC网页端的直播间地址）:\n')
            with open(state.url_config_file, 'w', encoding=state.text_encoding) as f:
                f.write(input_url)
    except OSError as err:
        logger.error(f"发生 I/O 错误: {err}")


def parse_url_config() -> None:
    """Parse ``URL_config.ini`` and append validated triples to ``url_tuples_list``."""
    state.url_comments, line_list, url_line_list = [], [], []
    with open(state.url_config_file, "r", encoding=state.text_encoding, errors='ignore') as file:
        for origin_line in file:
            if origin_line in line_list:
                delete_line(state.url_config_file, origin_line)
            line_list.append(origin_line)
            line = origin_line.strip()
            if len(line) < 18:
                continue

            line_split = line.split('主播: ')
            if len(line_split) > 2:
                line = update_file(
                    state.url_config_file, line,
                    f'{line_split[0]}主播: {line_split[-1]}',
                )

            is_comment_line = line.startswith("#")
            if is_comment_line:
                line = line.lstrip('#')

            if re.search('[,，]', line):
                split_line = re.split('[,，]', line)
            else:
                split_line = [line, '']

            if len(split_line) == 1:
                url = split_line[0]
                quality, name = state.video_record_quality, ''
            elif len(split_line) == 2:
                if contains_url(split_line[0]):
                    quality = state.video_record_quality
                    url, name = split_line
                else:
                    quality, url = split_line
                    name = ''
            else:
                quality, url, name = split_line

            if quality not in state.QUALITY_CHOICES:
                quality = '原画'

            if url not in url_line_list:
                url_line_list.append(url)
            else:
                delete_line(state.url_config_file, origin_line)

            url = 'https://' + url if '://' not in url else url
            url_host = url.split('/')[2]

            if 'live.shopee.' in url_host or '.shp.ee' in url_host:
                url_host = 'live.shopee.' if 'live.shopee.' in url_host else '.shp.ee'

            if url_host in state.ALL_PLATFORM_HOST or any(ext in url for ext in (".flv", ".m3u8")):
                if url_host in state.CLEAN_URL_HOST_LIST:
                    url = update_file(
                        state.url_config_file, old_str=url,
                        new_str=url.split('?')[0],
                    )

                if 'xiaohongshu' in url:
                    host_id = re.search('&host_id=(.*?)(?=&|$)', url)
                    if host_id:
                        new_url = url.split('?')[0] + f'?host_id={host_id.group(1)}'
                        url = update_file(state.url_config_file, old_str=url, new_str=new_url)

                state.url_comments = [i for i in state.url_comments if url not in i]
                if is_comment_line:
                    state.url_comments.append(url)
                else:
                    state.url_tuples_list.append((quality, url, name))
            else:
                if not origin_line.startswith('#'):
                    state.color_obj.print_colored(
                        f"\r{origin_line.strip()} 本行包含未知链接.此条跳过",
                        state.color_obj.YELLOW,
                    )
                    update_file(
                        state.url_config_file, old_str=origin_line,
                        new_str=origin_line, start_str='#',
                    )

    while state.need_update_line_list:
        a = state.need_update_line_list.pop()
        replace_words = a.split('|')
        if replace_words[0] != replace_words[1]:
            if replace_words[1].startswith("#"):
                start_with = '#'
                new_word = replace_words[1][1:]
            else:
                start_with = None
                new_word = replace_words[1]
            update_file(
                state.url_config_file, old_str=replace_words[0],
                new_str=new_word, start_str=start_with,
            )

    state.text_no_repeat_url = list(set(state.url_tuples_list))
