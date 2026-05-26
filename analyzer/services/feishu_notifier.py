from __future__ import annotations

import json
import os
import urllib.request

from legacy_core.utils import load_config


def get_feishu_webhook_url() -> str:
    env_value = os.getenv('FEISHU_BOT_WEBHOOK', '').strip()
    if env_value:
        return env_value
    try:
        cfg = load_config('config.yaml')
    except Exception:
        return ''
    flat_value = str(cfg.get('feishu.webhook_url') or '').strip()
    if flat_value:
        return flat_value
    return str((cfg.get('feishu') or {}).get('webhook_url') or '').strip()


def send_feishu_post_message(title: str, paragraphs: list[list[dict]], webhook_url: str | None = None) -> bool:
    url = (webhook_url or get_feishu_webhook_url()).strip()
    if not url:
        return False

    payload = {
        'msg_type': 'post',
        'content': {
            'post': {
                'zh_cn': {
                    'title': title,
                    'content': paragraphs,
                },
            },
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return 200 <= response.status < 300


def text_node(text: str) -> dict:
    return {'tag': 'text', 'text': text}