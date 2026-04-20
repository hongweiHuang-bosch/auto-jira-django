from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask


class IssueProcessWorkerTests(TestCase):
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
            issue_key='CHER-300',
            summary='空调异常',
            assignee='alice',
        )

    @patch('analyzer.management.commands.run_task_worker.run_issue_process_task')
    def test_worker_executes_pending_issue_process_task(self, mock_run):
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='PENDING',
        )

        def fake_run(task_id):
            task = IssueProcessTask.objects.get(pk=task_id)
            task.status = 'SUCCESS'
            task.progress = 100
            task.finished_at = timezone.now()
            task.save(update_fields=['status', 'progress', 'finished_at', 'updated_at'])
            IssueProcessResult.objects.create(
                process_task=task,
                issue_key=task.issue_key,
                summary=task.summary,
                reply_text='分析完成',
                result_status='SUCCESS',
            )

        mock_run.side_effect = fake_run

        call_command('run_task_worker', '--once')

        process_task.refresh_from_db()
        self.assertEqual(process_task.status, 'SUCCESS')
        self.assertEqual(process_task.progress, 100)
        self.assertTrue(IssueProcessResult.objects.filter(process_task=process_task).exists())
        mock_run.assert_called_once_with(process_task.pk)
