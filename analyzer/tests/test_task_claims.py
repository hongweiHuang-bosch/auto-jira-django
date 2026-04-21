from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessTask
from analyzer.services.task_claims import (
    claim_pending_filter_task,
    claim_pending_issue_process_task,
    recover_stale_issue_process_tasks,
)


class TaskClaimsTests(TestCase):
    def setUp(self):
        self.filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        self.snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=self.filter_task,
            issue_key='CHER-700',
            summary='claim 测试',
            assignee='alice',
        )

    def test_claim_pending_filter_task_marks_task_running(self):
        pending_task = FilterTask.objects.create(
            role_index=1,
            role_label='规则组 2',
            jql='project = CHER AND status = Open',
            status='PENDING',
        )

        claimed_id = claim_pending_filter_task()

        pending_task.refresh_from_db()
        self.assertEqual(claimed_id, pending_task.id)
        self.assertEqual(pending_task.status, 'RUNNING')
        self.assertEqual(pending_task.message, '正在执行 JQL 查询')
        self.assertIsNotNone(pending_task.started_at)

    def test_claim_pending_issue_process_task_marks_task_running(self):
        task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='PENDING',
            stage='PREPARING',
        )

        claimed_id = claim_pending_issue_process_task()

        task.refresh_from_db()
        self.assertEqual(claimed_id, task.id)
        self.assertEqual(task.status, 'RUNNING')
        self.assertEqual(task.message, '单票处理任务已领取')
        self.assertIsNotNone(task.started_at)

    def test_recover_stale_issue_process_tasks_marks_timeout_failed(self):
        task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='RUNNING',
            stage='PARSING',
            progress=35,
        )
        IssueProcessTask.objects.filter(pk=task.pk).update(
            updated_at=timezone.now() - timedelta(minutes=31)
        )

        recovered = recover_stale_issue_process_tasks(timeout_minutes=30)

        task.refresh_from_db()
        self.assertEqual(recovered, 1)
        self.assertEqual(task.status, 'FAILED')
        self.assertIn('超过 30 分钟无进展', task.error_message)
        self.assertIsNotNone(task.finished_at)
