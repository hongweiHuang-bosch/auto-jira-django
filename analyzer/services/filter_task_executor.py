from __future__ import annotations

import logging
import os
from concurrent.futures import Future, ThreadPoolExecutor

from django.db import close_old_connections
from django.utils import timezone

from analyzer.models import FilterTask
from analyzer.services.filter_task_runner import run_filter_task
from analyzer.services.rule_group_stream import publish_rule_group_snapshot

logger = logging.getLogger('jira_analyzer_worker')

_max_workers = int(os.getenv('FILTER_TASK_MAX_WORKERS', '2'))
_executor = ThreadPoolExecutor(max_workers=max(1, _max_workers), thread_name_prefix='filter-task')


def _claim_filter_task(task_id: int) -> bool:
    updated = FilterTask.objects.filter(pk=task_id, status='PENDING').update(
        status='RUNNING',
        started_at=timezone.now(),
        message='正在执行 JQL 查询',
    )
    if updated:
        publish_rule_group_snapshot()
    return bool(updated)


def _run_claimed_filter_task(task_id: int) -> None:
    close_old_connections()
    try:
        if not _claim_filter_task(task_id):
            logger.info('skip filter task execution because task is not pending', extra={'filter_task_id': task_id})
            return
        run_filter_task(task_id)
    finally:
        close_old_connections()


def submit_filter_task(task_id: int) -> Future:
    return _executor.submit(_run_claimed_filter_task, task_id)
