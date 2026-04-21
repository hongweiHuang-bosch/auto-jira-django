from __future__ import annotations

from django.db.models import Count, OuterRef, Q, Subquery

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask
from analyzer.serializers import (
    FilterTaskSerializer,
    FilteredIssueSnapshotSerializer,
    IssueProcessResultSerializer,
)
from .task_catalog import list_role_options


def _group_options_map():
    return {option['role_index']: option for option in list_role_options()}


def _next_action_for_issue(task_data, result_data):
    if task_data is None:
        return 'start_process'
    if task_data['status'] in ['PENDING', 'RUNNING']:
        return 'processing'
    if task_data['status'] == 'FAILED':
        return 'retry_process'
    if result_data:
        return 'view_result'
    return 'rerun_process'


def _empty_issue_page(page, page_size):
    return {'total': 0, 'page': page, 'page_size': page_size, 'items': []}


def _fetch_issue_page(filter_task, page, page_size):
    latest_task_id = Subquery(
        IssueProcessTask.objects.filter(snapshot_id=OuterRef('pk'))
        .order_by('-created_at')
        .values('id')[:1]
    )
    offset = (page - 1) * page_size
    issue_qs = (
        FilteredIssueSnapshot.objects.filter(filter_task=filter_task)
        .annotate(latest_process_task_id=latest_task_id)
        .order_by('issue_key')
    )
    issue_page = list(issue_qs[offset:offset + page_size])

    latest_task_ids = [issue.latest_process_task_id for issue in issue_page if issue.latest_process_task_id]
    task_map = {}
    result_map = {}
    if latest_task_ids:
        latest_tasks = IssueProcessTask.objects.filter(id__in=latest_task_ids).values(
            'id',
            'filter_task_id',
            'snapshot_id',
            'issue_key',
            'summary',
            'status',
            'stage',
            'progress',
            'message',
            'error_message',
            'started_at',
            'finished_at',
            'created_at',
            'updated_at',
        )
        task_map = {task['id']: dict(task) for task in latest_tasks}
        latest_results = IssueProcessResult.objects.filter(process_task_id__in=latest_task_ids)
        result_map = {result.process_task_id: IssueProcessResultSerializer(result).data for result in latest_results}

    items = []
    for issue in issue_page:
        task_data = task_map.get(issue.latest_process_task_id)
        result_data = result_map.get(issue.latest_process_task_id)
        items.append({
            'id': issue.id,
            'issue_key': issue.issue_key,
            'summary': issue.summary,
            'assignee': issue.assignee,
            'issue_updated_at': issue.issue_updated_at,
            'latest_process_task': task_data,
            'latest_result': result_data,
            'next_action': _next_action_for_issue(task_data, result_data),
        })

    return {
        'total': issue_qs.count(),
        'page': page,
        'page_size': page_size,
        'items': items,
    }


def build_rule_group_payload():
    latest_tasks = {}
    for task in FilterTask.objects.order_by('role_index', '-created_at'):
        latest_tasks.setdefault(task.role_index, task)

    issue_stats_rows = (
        IssueProcessTask.objects.values('filter_task__role_index')
        .annotate(
            running=Count('id', filter=Q(status='RUNNING')),
            success=Count('id', filter=Q(status='SUCCESS')),
            failed=Count('id', filter=Q(status='FAILED')),
        )
    )
    stats_map = {
        row['filter_task__role_index']: {
            'running': row['running'],
            'success': row['success'],
            'failed': row['failed'],
        }
        for row in issue_stats_rows
    }

    payload = []
    for option in list_role_options():
        filter_task = latest_tasks.get(option['role_index'])
        payload.append({
            **option,
            'latest_filter_task': FilterTaskSerializer(filter_task).data if filter_task else None,
            'issue_stats': stats_map.get(option['role_index'], {'running': 0, 'success': 0, 'failed': 0}),
        })
    return payload


def build_rule_group_detail(role_index, page=1, page_size=20):
    options_map = _group_options_map()
    group = options_map.get(role_index)
    if group is None:
        return {'group': None, 'filter_task': None, 'issues': _empty_issue_page(page, page_size)}

    filter_task = FilterTask.objects.filter(role_index=role_index).order_by('-created_at').first()
    if filter_task is None:
        return {'group': group, 'filter_task': None, 'issues': _empty_issue_page(page, page_size)}

    return {
        'group': group,
        'filter_task': FilterTaskSerializer(filter_task).data,
        'issues': _fetch_issue_page(filter_task, page, page_size),
    }


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
    return _fetch_issue_page(filter_task, page, page_size)
