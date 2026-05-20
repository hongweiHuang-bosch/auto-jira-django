from __future__ import annotations

import json
import logging
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from analyzer.models import IssueValidationCheck, IssueValidationRun
from analyzer.services.cantrace_payload import parse_cantrace_summary
from analyzer.services.issue_validation_service import build_validation_payload

logger = logging.getLogger('jira_analyzer_worker')


def run_issue_validation_run(run_id: int):
    run = IssueValidationRun.objects.select_related('process_result').get(pk=run_id)
    try:
        result = run.process_result
        payload = build_validation_payload(
            reply_text=result.reply_text,
            cantrace_payload=_load_cantrace_payload(result),
            upper_requirement_text=_load_upper_requirement_text(result),
            upper_comment_text=result.upper_comment or '',
        )

        run.status = 'SUCCESS'
        run.system_verdict = payload['system_verdict']
        run.summary_reason = payload['summary_reason']
        run.evidence_payload = {'table_rows': payload.get('table_rows', [])}
        run.chart_payload = payload.get('chart_payload', {})
        run.error_message = ''
        run.finished_at = timezone.now()
        run.save(update_fields=[
            'status',
            'system_verdict',
            'summary_reason',
            'evidence_payload',
            'chart_payload',
            'error_message',
            'finished_at',
            'updated_at',
        ])

        run.checks.all().delete()
        IssueValidationCheck.objects.bulk_create([
            IssueValidationCheck(
                validation_run=run,
                check_type=check.get('check_type', ''),
                status=check.get('status', 'UNKNOWN'),
                title=check.get('title', ''),
                reason=check.get('reason', ''),
                evidence_payload=check.get('evidence_payload', {}),
                sort_order=check.get('sort_order', 0),
            )
            for check in payload.get('checks', [])
        ])
        logger.info('validation run completed', extra={'validation_run_id': run.id})
    except Exception as exc:
        run.status = 'FAILED'
        run.error_message = str(exc)
        run.finished_at = timezone.now()
        run.save(update_fields=['status', 'error_message', 'finished_at', 'updated_at'])
        logger.exception('validation run failed', extra={'validation_run_id': run.id})


def _load_cantrace_payload(result) -> dict | None:
    payload = _load_cantrace_payload_from_raw_signals(result.raw_signals)
    if payload is not None:
        logger.info(
            'loaded cantrace payload from raw_signals issue=%s signal_count=%s',
            result.issue_key,
            len(payload.get('signals', [])),
        )
        return payload
    logger.warning('raw_signals unavailable for issue=%s, falling back to cantrace text file', result.issue_key)
    return _load_cantrace_payload_from_text_file(result)


def _load_cantrace_payload_from_raw_signals(raw_signals: str) -> dict | None:
    if not raw_signals:
        return None
    try:
        payload = json.loads(raw_signals)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None

    signals = payload.get('signals')
    if not isinstance(signals, list):
        return None
    if not all(isinstance(signal, dict) for signal in signals):
        return None
    return payload


def _load_cantrace_payload_from_text_file(result) -> dict | None:
    directory = _resolve_cantrace_directory(result)
    if directory is None or not directory.exists():
        logger.warning('cantrace directory missing for issue=%s directory=%s', result.issue_key, directory)
        return None

    candidates = sorted(directory.glob('*_can_trace.txt'))
    if not candidates:
        logger.warning('no *_can_trace.txt found for issue=%s directory=%s', result.issue_key, directory)
        return None

    signals = _parse_cantrace_text(candidates[0])
    logger.info(
        'loaded cantrace payload from text file issue=%s path=%s signal_count=%s',
        result.issue_key,
        candidates[0],
        len(signals),
    )
    return {'signals': signals} if signals else None


def _resolve_cantrace_directory(result) -> Path | None:
    image_path = result.can_trace_image or result.can_trace_image_url
    if not image_path:
        return None

    path_text = str(image_path).lstrip('/')
    if path_text.startswith('media/'):
        relative = path_text[len('media/'):]
        return (Path(settings.MEDIA_ROOT) / relative).parent

    path = Path(path_text)
    if path.is_absolute():
        return path.parent
    return (Path(settings.BASE_DIR) / path).parent


def _parse_cantrace_text(path: Path) -> list[dict]:
    return parse_cantrace_summary(path.read_text(encoding='utf-8', errors='ignore'))


def _load_upper_requirement_text(result) -> str:
    return result.summary or ''
