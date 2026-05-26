from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessTask
from analyzer.serializers import FilterTaskSerializer, IssueProcessTaskSerializer
from analyzer.services.task_catalog import get_role_entry, get_role_label, list_role_options


FILTER_TASK_STALE_TIMEOUT = timedelta(minutes=10)


def prepare_filter_task(role_index: int) -> dict:
    try:
        role_entry = get_role_entry(role_index)
    except (IndexError, ValueError):
        return {
            'status': 'failed',
            'detail': '无效的规则组索引',
            'task': None,
            'role_label': f'规则组 {role_index + 1}',
        }

    running = FilterTask.objects.filter(role_index=role_index, status__in=['PENDING', 'RUNNING']).first()
    if running:
        if running.updated_at < timezone.now() - FILTER_TASK_STALE_TIMEOUT:
            running.status = 'EXPIRED'
            running.message = '筛票超时，已被新任务替换'
            running.save(update_fields=['status', 'message', 'updated_at'])
        else:
            return {
                'status': 'conflict',
                'detail': '该规则组已有进行中的筛票任务',
                'task': running,
                'role_label': get_role_label(role_index, role_entry),
            }

    task = FilterTask.objects.create(
        role_index=role_index,
        role_label=get_role_label(role_index, role_entry),
        jql=role_entry.get('jql', ''),
        status='PENDING',
        message='筛票任务已创建',
    )
    return {
        'status': 'created',
        'detail': '筛票任务已创建',
        'task': task,
        'role_label': task.role_label,
    }


def prepare_issue_process_task(filter_task: FilterTask, snapshot: FilteredIssueSnapshot) -> dict:
    running = IssueProcessTask.objects.filter(
        issue_key=snapshot.issue_key,
        status__in=['PENDING', 'RUNNING'],
    ).order_by('-created_at').first()
    if running is not None:
        return {
            'status': 'conflict',
            'detail': '当前票已有进行中的处理任务',
            'task': running,
        }

    process_task = IssueProcessTask.objects.create(
        filter_task=filter_task,
        snapshot=snapshot,
        issue_key=snapshot.issue_key,
        summary=snapshot.summary,
        status='PENDING',
        stage='PREPARING',
        message='单票处理任务已创建',
    )
    return {
        'status': 'created',
        'detail': '单票处理任务已创建',
        'task': process_task,
    }


def create_bulk_filter_tasks() -> tuple[dict, list[int]]:
    summary = {
        'total_groups': 0,
        'created': 0,
        'skipped_conflict': 0,
        'failed': 0,
    }
    items = []
    created_task_ids = []

    for option in list_role_options():
        role_index = option['role_index']
        summary['total_groups'] += 1
        outcome = prepare_filter_task(role_index)
        task = outcome['task']

        if outcome['status'] == 'created':
            summary['created'] += 1
            created_task_ids.append(task.id)
        elif outcome['status'] == 'conflict':
            summary['skipped_conflict'] += 1
        else:
            summary['failed'] += 1

        items.append({
            'role_index': role_index,
            'role_label': outcome['role_label'],
            'status': outcome['status'],
            'detail': outcome['detail'],
            'filter_task': FilterTaskSerializer(task).data if task else None,
        })

    return {'summary': summary, 'items': items}, created_task_ids


def create_bulk_issue_process_tasks() -> tuple[dict, bool]:
    summary = {
        'total_groups': 0,
        'groups_with_filter': 0,
        'created': 0,
        'skipped_conflict': 0,
        'skipped_without_filter': 0,
        'failed': 0,
    }
    items = []
    created_any = False

    for option in list_role_options():
        role_index = option['role_index']
        role_label = option['role_label']
        summary['total_groups'] += 1
        latest_filter_task = FilterTask.objects.filter(role_index=role_index).order_by('-created_at').first()

        if latest_filter_task is None or latest_filter_task.status in ['PENDING', 'RUNNING']:
            summary['skipped_without_filter'] += 1
            items.append({
                'role_index': role_index,
                'role_label': role_label,
                'filter_task_id': latest_filter_task.id if latest_filter_task else None,
                'status': 'no_filter',
                'detail': '当前规则组没有可用的筛票结果',
                'total_issues': 0,
                'created': 0,
                'skipped_conflict': 0,
                'failed': 0,
                'tasks': [],
            })
            continue

        summary['groups_with_filter'] += 1
        snapshots = list(FilteredIssueSnapshot.objects.filter(filter_task=latest_filter_task).order_by('issue_key'))
        item = {
            'role_index': role_index,
            'role_label': role_label,
            'filter_task_id': latest_filter_task.id,
            'status': 'processed',
            'detail': '批量处理任务已完成发起',
            'total_issues': len(snapshots),
            'created': 0,
            'skipped_conflict': 0,
            'failed': 0,
            'tasks': [],
        }

        for snapshot in snapshots:
            outcome = prepare_issue_process_task(latest_filter_task, snapshot)
            task = outcome['task']
            item['tasks'].append({
                'issue_key': snapshot.issue_key,
                'status': outcome['status'],
                'detail': outcome['detail'],
                'process_task': IssueProcessTaskSerializer(task).data if task else None,
            })
            if outcome['status'] == 'created':
                summary['created'] += 1
                item['created'] += 1
                created_any = True
            elif outcome['status'] == 'conflict':
                summary['skipped_conflict'] += 1
                item['skipped_conflict'] += 1
            else:
                summary['failed'] += 1
                item['failed'] += 1

        items.append(item)

    return {'summary': summary, 'items': items}, created_any