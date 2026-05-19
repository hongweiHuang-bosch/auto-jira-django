from __future__ import annotations

import json
import logging

from django.utils import timezone

from analyzer.models import IssueValidationCheck, IssueValidationRun
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
    if not result.raw_signals:
        return None
    try:
        payload = json.loads(result.raw_signals)
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


def _load_upper_requirement_text(result) -> str:
    return result.summary or ''
