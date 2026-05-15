from __future__ import annotations

from django.db.models import Count, OuterRef, Q, Subquery

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask
from analyzer.serializers import (
    FilterTaskSerializer,
    FilteredIssueSnapshotSerializer,
    IssueProcessTaskSerializer,
    IssueProcessResultSerializer,
)
from analyzer.services.jira_issue_payload import build_jira_url
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


def _serialize_processed_issue(task, process_count):
    result = getattr(task, 'result', None)
    snapshot = task.snapshot
    return {
        'issue_key': task.issue_key,
        'summary': task.summary or snapshot.summary,
        'assignee': snapshot.assignee,
        'issue_updated_at': snapshot.issue_updated_at,
        'filter_task': FilterTaskSerializer(task.filter_task).data,
        'latest_process_task': IssueProcessTaskSerializer(task).data,
        'latest_result': IssueProcessResultSerializer(result).data if result else None,
        'process_count': process_count,
    }


def build_processed_issue_page(role_index, page=1, page_size=20, query='', status=''):
    qs = (
        IssueProcessTask.objects.filter(filter_task__role_index=role_index)
        .select_related('filter_task', 'snapshot', 'result')
        .order_by('-created_at', '-id')
    )
    query = (query or '').strip()
    status = (status or '').strip()

    process_counts = {
        row['issue_key']: row['total']
        for row in IssueProcessTask.objects.filter(filter_task__role_index=role_index)
        .values('issue_key')
        .annotate(total=Count('id'))
    }

    latest_by_issue = []
    seen_issue_keys = set()
    for task in qs:
        if task.issue_key in seen_issue_keys:
            continue
        seen_issue_keys.add(task.issue_key)
        if query:
            searchable_text = f'{task.issue_key} {task.summary} {task.snapshot.summary}'.lower()
            if query.lower() not in searchable_text:
                continue
        if status and task.status != status:
            continue
        latest_by_issue.append(task)

    offset = (page - 1) * page_size
    page_items = latest_by_issue[offset:offset + page_size]
    return {
        'total': len(latest_by_issue),
        'page': page,
        'page_size': page_size,
        'items': [
            _serialize_processed_issue(task, process_counts.get(task.issue_key, 0))
            for task in page_items
        ],
    }


def build_processed_issue_detail(role_index, issue_key):
    tasks = list(
        IssueProcessTask.objects.filter(
            filter_task__role_index=role_index,
            issue_key=issue_key,
        )
        .select_related('filter_task', 'snapshot', 'result')
        .order_by('-created_at', '-id')
    )
    if not tasks:
        return None

    latest_task = tasks[0]
    group = _group_options_map().get(role_index)
    records = []
    for task in tasks:
        result = getattr(task, 'result', None)
        records.append({
            'filter_task': FilterTaskSerializer(task.filter_task).data,
            'snapshot': {
                'id': task.snapshot_id,
                'issue_key': task.snapshot.issue_key,
                'summary': task.snapshot.summary,
                'assignee': task.snapshot.assignee,
                'issue_updated_at': task.snapshot.issue_updated_at,
                'created_at': task.snapshot.created_at,
                'updated_at': task.snapshot.updated_at,
            },
            'process_task': IssueProcessTaskSerializer(task).data,
            'result': IssueProcessResultSerializer(result).data if result else None,
        })

    return {
        'group': group,
        'issue_key': issue_key,
        'jira_url': build_jira_url(issue_key),
        'summary': latest_task.summary or latest_task.snapshot.summary,
        'assignee': latest_task.snapshot.assignee,
        'records': records,
    }
