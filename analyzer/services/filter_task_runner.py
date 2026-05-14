from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from analyzer.models import FilterTask, FilteredIssueSnapshot
from analyzer.services.rule_group_stream import publish_rule_group_snapshot
from legacy_core.jira_utils import JiraClient
from legacy_core.utils import load_config

logger = logging.getLogger('jira_analyzer_worker')


def _assignee_name(issue):
    assignee = getattr(getattr(issue, 'fields', None), 'assignee', None)
    return getattr(assignee, 'displayName', '') if assignee else ''


def run_filter_task(task_id: int):
    task = FilterTask.objects.get(pk=task_id)
    try:
        cfg = load_config('config.yaml')
        jira_cfg = cfg['jira']
        jira = JiraClient(
            server=jira_cfg['server'],
            username=jira_cfg['username'],
            password=jira_cfg['password'],
            use_system_proxy=jira_cfg.get('use_system_proxy', True),
            proxies=jira_cfg.get('proxies'),
        )

        issues = jira.search_issues(task.jql, expand='changelog')
        FilteredIssueSnapshot.objects.filter(filter_task=task).delete()
        for issue in issues:
            FilteredIssueSnapshot.objects.create(
                filter_task=task,
                issue_key=issue.key,
                summary=getattr(issue.fields, 'summary', '') or '',
                assignee=_assignee_name(issue),
            )

        task.status = 'SUCCESS'
        task.issue_count = len(issues)
        task.finished_at = timezone.now()
        task.expires_at = timezone.now() + timedelta(hours=24)
        task.message = f'筛票完成，共 {len(issues)} 张票'
        task.save(update_fields=['status', 'issue_count', 'finished_at', 'expires_at', 'message', 'updated_at'])
        publish_rule_group_snapshot()
        logger.info('filter task succeeded', extra={'filter_task_id': task.id, 'issue_count': len(issues)})
    except Exception as e:
        task.status = 'FAILED'
        task.error_message = str(e)
        task.finished_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'finished_at', 'updated_at'])
        publish_rule_group_snapshot()
        logger.exception('filter task failed', extra={'filter_task_id': task.id})
