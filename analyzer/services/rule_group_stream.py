from __future__ import annotations

import json
import queue
import threading
from typing import Iterator

from .rule_group_payload import build_rule_group_payload


_subscribers = {}
_subscribers_lock = threading.Lock()
_next_subscriber_id = 1


def _subscribe():
    global _next_subscriber_id
    subscriber_queue = queue.Queue()
    with _subscribers_lock:
        subscriber_id = _next_subscriber_id
        _next_subscriber_id += 1
        _subscribers[subscriber_id] = subscriber_queue
    return subscriber_id, subscriber_queue


def _unsubscribe(subscriber_id):
    with _subscribers_lock:
        _subscribers.pop(subscriber_id, None)


def _format_sse(payload):
    return f"event: groups\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def publish_rule_group_snapshot():
    payload = build_rule_group_payload()
    for subscriber_queue in list(_subscribers.values()):
        subscriber_queue.put(payload)


def stream_rule_group_events() -> Iterator[str]:
    subscriber_id, subscriber_queue = _subscribe()
    try:
        yield _format_sse(build_rule_group_payload())
        while True:
            try:
                payload = subscriber_queue.get(timeout=15)
                yield _format_sse(payload)
            except queue.Empty:
                yield ': ping\n\n'
    finally:
        _unsubscribe(subscriber_id)
