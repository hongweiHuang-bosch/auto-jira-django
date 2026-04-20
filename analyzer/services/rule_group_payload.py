from __future__ import annotations

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessTask
from analyzer.serializers import FilterTaskSerializer, FilteredIssueSnapshotSerializer
from .task_catalog import list_role_options


def build_rule_group_payload():
    latest_tasks = {}
    for task in FilterTask.objects.all().order_by('role_index', '-created_at'):
        latest_tasks.setdefault(task.role_index, task)

    payload = []
    for option in list_role_options():
        filter_task = latest_tasks.get(option['role_index'])
        task_data = FilterTaskSerializer(filter_task).data if filter_task else None
        issue_stats = {
            'running': IssueProcessTask.objects.filter(filter_task__role_index=option['role_index'], status='RUNNING').count(),
            'success': IssueProcessTask.objects.filter(filter_task__role_index=option['role_index'], status='SUCCESS').count(),
            'failed': IssueProcessTask.objects.filter(filter_task__role_index=option['role_index'], status='FAILED').count(),
        }
        payload.append({
            **option,
            'latest_filter_task': task_data,
            'issue_stats': issue_stats,
        })
    return payload


def get_latest_filter_task_detail(role_index, include_issues=False, page_size=20):
    task = FilterTask.objects.filter(role_index=role_index).order_by('-created_at').first()
    if task is None:
        return {'filter_task': None, 'issues': {'total': 0, 'items': []}}

    issue_qs = FilteredIssueSnapshot.objects.filter(filter_task=task).order_by('issue_key')
    issue_items = list(issue_qs[:page_size]) if include_issues else []
    return {
        'filter_task': FilterTaskSerializer(task).data,
        'issues': {
            'total': issue_qs.count(),
            'items': FilteredIssueSnapshotSerializer(issue_items, many=True).data,
        },
    }


def get_filter_task_issue_page(filter_task, page=1, page_size=20):
    offset = (page - 1) * page_size
    issue_qs = FilteredIssueSnapshot.objects.filter(filter_task=filter_task).order_by('issue_key')
    return {
        'total': issue_qs.count(),
        'page': page,
        'page_size': page_size,
        'items': FilteredIssueSnapshotSerializer(issue_qs[offset:offset + page_size], many=True).data,
    }
