from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from analyzer.models import FilterTask, IssueProcessTask

logger = logging.getLogger('jira_analyzer_worker')


def claim_pending_filter_task(now=None):
    current = now or timezone.now()
    with transaction.atomic():
        task = (
            FilterTask.objects.select_for_update(skip_locked=True)
            .filter(status='PENDING')
            .order_by('created_at')
            .first()
        )
        if task is None:
            return None
        task.status = 'RUNNING'
        task.started_at = current
        task.message = '正在执行 JQL 查询'
        task.save(update_fields=['status', 'started_at', 'message', 'updated_at'])
        logger.info('claimed filter task', extra={'filter_task_id': task.id, 'role_index': task.role_index})
        return task.id


def claim_pending_issue_process_task(now=None):
    current = now or timezone.now()
    with transaction.atomic():
        task = (
            IssueProcessTask.objects.select_for_update(skip_locked=True)
            .filter(status='PENDING')
            .order_by('created_at')
            .first()
        )
        if task is None:
            return None
        task.status = 'RUNNING'
        task.started_at = current
        task.stage = 'PREPARING'
        task.message = '单票处理任务已领取'
        task.save(update_fields=['status', 'started_at', 'stage', 'message', 'updated_at'])
        logger.info(
            'claimed process task',
            extra={
                'process_task_id': task.id,
                'filter_task_id': task.filter_task_id,
                'issue_key': task.issue_key,
            },
        )
        return task.id


def recover_stale_issue_process_tasks(timeout_minutes=30, now=None):
    current = now or timezone.now()
    cutoff = current - timedelta(minutes=timeout_minutes)
    stale_qs = IssueProcessTask.objects.filter(status='RUNNING', updated_at__lt=cutoff)
    recovered = stale_qs.update(
        status='FAILED',
        error_message=f'任务超过 {timeout_minutes} 分钟无进展，已由 worker 标记失败',
        finished_at=current,
    )
    if recovered:
        logger.warning('recovered stale process tasks', extra={'count': recovered})
    return recovered
