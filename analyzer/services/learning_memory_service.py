from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction

from analyzer.models import IssueLearningMemory, IssueProcessResult

logger = logging.getLogger(__name__)


def _memory_root() -> Path:
    return Path(settings.LEARNING_MEMORY_ROOT)


def _memory_path(role_index: int, issue_key: str) -> Path:
    return _memory_root() / f'role_{role_index}' / f'{issue_key}.json'


def _json_default(value: Any, *, default: Any) -> Any:
    if value is None:
        return default
    return value


def _normalize_text(text: str) -> str:
    text = (text or '').lower()
    text = re.sub(r'[^0-9a-z\u4e00-\u9fff_]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _extract_keywords(*parts: str) -> list[str]:
    text = _normalize_text(' '.join(parts))
    keywords = re.findall(r'[0-9a-z_]+|[\u4e00-\u9fff]{2,}', text)
    seen = set()
    ordered = []
    for item in keywords:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _build_memory_payload(result: IssueProcessResult, existing: IssueLearningMemory | None = None) -> dict[str, Any]:
    process_task = result.process_task
    now = result.manual_review_saved_at or result.reviewed_at or result.updated_at
    created_at = existing.created_at if existing is not None else now
    updated_at = now
    return {
        'role_index': process_task.filter_task.role_index,
        'issue_key': result.issue_key or '',
        'requirements': '',
        'comment': '',
        'signal_summary': result.raw_signals or '',
        'qnx_android_logs': '',
        'cantrace_output': '',
        'incorrect_conclusion': result.reply_text or '',
        'error_reason': result.manual_error_reason or result.review_reason or '',
        'correct_result': result.manual_correct_result or '',
        'review_status': result.review_status or '',
        'created_at': created_at.isoformat() if created_at else '',
        'updated_at': updated_at.isoformat() if updated_at else '',
    }


def _serialize_payload(payload: dict[str, Any]) -> tuple[str, str]:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    return serialized, digest


def persist_learning_memory(result: IssueProcessResult) -> IssueLearningMemory:
    role_index = result.process_task.filter_task.role_index
    existing = IssueLearningMemory.objects.filter(role_index=role_index, issue_key=result.issue_key).first()
    payload = _build_memory_payload(result, existing=existing)
    serialized, digest = _serialize_payload(payload)
    file_path = _memory_path(role_index, result.issue_key)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix('.json.tmp')
    tmp_path.write_text(serialized, encoding='utf-8')
    tmp_path.replace(file_path)

    with transaction.atomic():
        memory, created = IssueLearningMemory.objects.select_for_update().get_or_create(
            role_index=role_index,
            issue_key=result.issue_key,
            defaults={
                'review_status': payload['review_status'],
                'incorrect_conclusion': payload['incorrect_conclusion'],
                'correct_conclusion': payload['correct_result'],
                'error_reason': payload['error_reason'],
                'signal_summary': payload['signal_summary'],
                'memory_file_path': str(file_path),
                'memory_content_hash': digest,
            },
        )
        if not created:
            memory.review_status = payload['review_status']
            memory.incorrect_conclusion = payload['incorrect_conclusion']
            memory.correct_conclusion = payload['correct_result']
            memory.error_reason = payload['error_reason']
            memory.signal_summary = payload['signal_summary']
            memory.memory_file_path = str(file_path)
            memory.memory_content_hash = digest
            memory.save(update_fields=[
                'review_status',
                'incorrect_conclusion',
                'correct_conclusion',
                'error_reason',
                'signal_summary',
                'memory_file_path',
                'memory_content_hash',
                'updated_at',
            ])
    return memory


def delete_learning_memory(role_index: int, issue_key: str) -> None:
    memory = IssueLearningMemory.objects.filter(role_index=role_index, issue_key=issue_key).first()
    if memory is None:
        return
    file_path = Path(memory.memory_file_path)
    memory.delete()
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        logger.warning('Failed to remove learning memory file %s', file_path, exc_info=True)


def _load_memory_content(memory: IssueLearningMemory) -> dict[str, Any] | None:
    try:
        file_path = Path(memory.memory_file_path)
        payload = json.loads(file_path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        logger.warning('Learning memory file missing: %s', memory.memory_file_path)
        return None
    except json.JSONDecodeError:
        logger.warning('Learning memory file is corrupted: %s', memory.memory_file_path)
        return None
    except OSError:
        logger.warning('Learning memory file read failed: %s', memory.memory_file_path, exc_info=True)
        return None

    return {
        'role_index': _json_default(payload.get('role_index'), default=memory.role_index),
        'issue_key': _json_default(payload.get('issue_key'), default=memory.issue_key),
        'requirements': _json_default(payload.get('requirements'), default=''),
        'comment': _json_default(payload.get('comment'), default=''),
        'signal_summary': _json_default(payload.get('signal_summary'), default=''),
        'qnx_android_logs': _json_default(payload.get('qnx_android_logs'), default=''),
        'cantrace_output': _json_default(payload.get('cantrace_output'), default=''),
        'incorrect_conclusion': _json_default(payload.get('incorrect_conclusion'), default=memory.incorrect_conclusion),
        'error_reason': _json_default(payload.get('error_reason'), default=memory.error_reason),
        'correct_result': _json_default(payload.get('correct_result'), default=memory.correct_conclusion),
        'review_status': _json_default(payload.get('review_status'), default=memory.review_status),
        'created_at': _json_default(payload.get('created_at'), default=''),
        'updated_at': _json_default(payload.get('updated_at'), default=''),
    }


def retrieve_learning_memories(
    *,
    role_index: int | None,
    summary: str = '',
    comment: str = '',
    requirements: str = '',
    signal_summary: str = '',
    max_count: int = 3,
) -> list[dict[str, Any]]:
    queryset = IssueLearningMemory.objects.all()
    if role_index is not None:
        queryset = queryset.filter(role_index=role_index)

    candidates = []
    keywords = _extract_keywords(summary, comment, requirements, signal_summary)
    for memory in queryset.order_by('-updated_at', '-id'):
        payload = _load_memory_content(memory)
        if payload is None:
            continue
        candidate_blob = _normalize_text(' '.join([
            payload['signal_summary'],
            payload['error_reason'],
            payload['incorrect_conclusion'],
            payload['correct_result'],
            payload['requirements'],
            payload['comment'],
        ]))
        score = 0
        for keyword in keywords:
            if keyword and keyword in candidate_blob:
                score += 1
        if role_index is not None and memory.role_index == role_index:
            score += 100
        if keywords and score == (100 if role_index is not None and memory.role_index == role_index else 0):
            continue
        candidates.append((score, memory.updated_at, payload))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [payload for _, _, payload in candidates[:max_count]]


def build_learning_memories_for_prompt(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return '暂无可复用的历史纠错记忆。'
    lines = []
    for index, memory in enumerate(memories, 1):
        context_bits = [memory.get('signal_summary', ''), memory.get('requirements', ''), memory.get('comment', '')]
        context_summary = ' / '.join([item for item in context_bits if item]) or '（上下文摘要缺失）'
        lines.append(
            f'【历史错例 {index}】\n'
            f'  Jira: {memory.get("issue_key", "")}\n'
            f'  错误结论: {memory.get("incorrect_conclusion", "")}\n'
            f'  正确结论: {memory.get("correct_result", "")}\n'
            f'  错误原因: {memory.get("error_reason", "")}\n'
            f'  上下文摘要: {context_summary}'
        )
    return '\n\n'.join(lines)
