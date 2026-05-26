from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from analyzer.models import AutoCycleState, FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask
from analyzer.services.bulk_task_actions import create_bulk_filter_tasks, prepare_issue_process_task
from analyzer.services.feishu_notifier import send_feishu_post_message, text_node
from analyzer.services.filter_task_executor import submit_filter_task
from analyzer.services.rule_group_stream import publish_rule_group_snapshot
from analyzer.services.task_catalog import list_role_options


def get_auto_cycle_state() -> AutoCycleState:
    state, _created = AutoCycleState.objects.get_or_create(
        pk=1,
        defaults={
            'is_running': False,
            'interval_minutes': 30,
            'stage': 'STOPPED',
            'stop_requested': False,
        },
    )
    return state


def start_auto_cycle(interval_minutes: int) -> AutoCycleState:
    if interval_minutes < 1:
        raise ValueError('interval_minutes 必须大于 0')

    now = timezone.now()
    state = get_auto_cycle_state()
    state.is_running = True
    state.interval_minutes = interval_minutes
    state.stage = 'IDLE'
    state.stop_requested = False
    state.last_error = ''
    state.last_started_at = now
    state.next_run_at = now
    state.save(update_fields=[
        'is_running',
        'interval_minutes',
        'stage',
        'stop_requested',
        'last_error',
        'last_started_at',
        'next_run_at',
        'updated_at',
    ])
    return state


def stop_auto_cycle() -> AutoCycleState:
    now = timezone.now()
    state = get_auto_cycle_state()
    state.is_running = False
    state.stage = 'STOPPED'
    state.stop_requested = True
    state.last_finished_at = now
    state.next_run_at = None
    state.save(update_fields=[
        'is_running',
        'stage',
        'stop_requested',
        'last_finished_at',
        'next_run_at',
        'updated_at',
    ])
    IssueProcessTask.objects.filter(status__in=['PENDING', 'RUNNING']).update(
        status='FAILED',
        error_message='用户停止周期任务，处理任务已取消',
        finished_at=now,
        updated_at=now,
    )
    publish_rule_group_snapshot()
    return state


def schedule_next_cycle(state: AutoCycleState, now=None) -> AutoCycleState:
    current = now or timezone.now()
    state.stage = 'IDLE'
    state.next_run_at = current + timedelta(minutes=state.interval_minutes)
    state.save(update_fields=['stage', 'next_run_at', 'updated_at'])
    return state


def _create_process_tasks_for_latest_filters() -> int:
    created = 0
    for option in list_role_options():
        latest_filter_task = FilterTask.objects.filter(
            role_index=option['role_index'],
            status='SUCCESS',
        ).order_by('-created_at').first()
        if latest_filter_task is None:
            continue

        snapshots = FilteredIssueSnapshot.objects.filter(filter_task=latest_filter_task).order_by('issue_key')
        for snapshot in snapshots:
            if IssueProcessTask.objects.filter(snapshot=snapshot).exists():
                continue
            outcome = prepare_issue_process_task(latest_filter_task, snapshot)
            if outcome['status'] == 'created':
                created += 1
    if created:
        publish_rule_group_snapshot()
    return created


def run_auto_cycle_once(now=None) -> AutoCycleState:
    current = now or timezone.now()
    state = get_auto_cycle_state()
    if not state.is_running or state.stop_requested:
        return state

    notify_finished_process_tasks()
    _create_process_tasks_for_latest_filters()

    if state.next_run_at and state.next_run_at > current:
        return state

    state.stage = 'FILTERING'
    state.last_error = ''
    state.save(update_fields=['stage', 'last_error', 'updated_at'])
    payload, created_task_ids = create_bulk_filter_tasks()
    for task_id in created_task_ids:
        submit_filter_task(task_id)
    if payload['summary']['failed']:
        state.last_error = f"{payload['summary']['failed']} 个规则组筛票任务创建失败"
        state.stage = 'ERROR'
        state.save(update_fields=['last_error', 'stage', 'updated_at'])
        return state
    return schedule_next_cycle(state, now=current)


def _build_feishu_paragraphs(task: IssueProcessTask) -> list[list[dict]]:
    result = getattr(task, 'result', None)
    status_label = '成功' if task.status == 'SUCCESS' else '失败'
    analysis_text = ''
    upper_comment = ''
    if isinstance(result, IssueProcessResult):
        analysis_text = result.reply_text or result.error_message or ''
        upper_comment = result.upper_comment or ''
    if not analysis_text:
        analysis_text = task.error_message or task.message or ''
    paragraphs = [
        [text_node(f'jira票号：{task.issue_key}')],
        [text_node(f'jira主题：{task.summary or "-"}')],
        [text_node(f'处理状态：{status_label}')],
    ]
    if upper_comment:
        paragraphs.append([text_node(f'jira描述/上层评论：{upper_comment}')])
    paragraphs.append([text_node(f'分析结果：{analysis_text or "-"}')])
    return paragraphs


def notify_finished_process_tasks() -> int:
    tasks = list(
        IssueProcessTask.objects.filter(
            status__in=['SUCCESS', 'FAILED'],
            feishu_notified_at__isnull=True,
        ).order_by('finished_at', 'id')
    )
    notified = 0
    now = timezone.now()
    for task in tasks:
        title = f'Jira 票处理{ "成功" if task.status == "SUCCESS" else "失败" }：{task.issue_key}'
        if send_feishu_post_message(title, _build_feishu_paragraphs(task)):
            IssueProcessTask.objects.filter(pk=task.pk, feishu_notified_at__isnull=True).update(
                feishu_notified_at=now,
                updated_at=now,
            )
            notified += 1
    return notified