from __future__ import annotations

import json
import queue
import threading
import time
from typing import Iterator

from .payloads import build_issue_list_payload


_subscribers: dict[int, list[queue.Queue]] = {}
_subscribers_lock = threading.Lock()
POLL_INTERVAL_SECONDS = 1
HEARTBEAT_INTERVAL_SECONDS = 15


def subscribe(user_id: int) -> queue.Queue:
    subscriber_queue: queue.Queue = queue.Queue()
    with _subscribers_lock:
        _subscribers.setdefault(user_id, []).append(subscriber_queue)
    return subscriber_queue


def unsubscribe(user_id: int, subscriber_queue: queue.Queue) -> None:
    with _subscribers_lock:
        queues = _subscribers.get(user_id, [])
        if subscriber_queue in queues:
            queues.remove(subscriber_queue)
        if not queues and user_id in _subscribers:
            _subscribers.pop(user_id, None)


def _format_sse(payload: dict) -> str:
    return f"event: geely2\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def publish_geely2_snapshot(user) -> None:
    payload = build_issue_list_payload(user)
    with _subscribers_lock:
        subscribers = list(_subscribers.get(user.id, []))
    for subscriber_queue in subscribers:
        subscriber_queue.put(payload)


def stream_geely2_events(user) -> Iterator[str]:
    subscriber_queue = subscribe(user.id)
    try:
        latest_payload = build_issue_list_payload(user)
        latest_payload_json = json.dumps(latest_payload, ensure_ascii=False)
        last_activity_at = time.monotonic()
        yield _format_sse(latest_payload)
        while True:
            try:
                payload = subscriber_queue.get(timeout=POLL_INTERVAL_SECONDS)
            except queue.Empty:
                payload = build_issue_list_payload(user)

            payload_json = json.dumps(payload, ensure_ascii=False)
            if payload_json != latest_payload_json:
                latest_payload_json = payload_json
                last_activity_at = time.monotonic()
                yield _format_sse(payload)
                continue

            if time.monotonic() - last_activity_at >= HEARTBEAT_INTERVAL_SECONDS:
                last_activity_at = time.monotonic()
                yield ': ping\n\n'
    finally:
        unsubscribe(user.id, subscriber_queue)