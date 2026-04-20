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

    @patch('analyzer.services.issue_analysis_service.load_config')
    @patch('analyzer.services.issue_analysis_service.JiraClient')
    @patch('analyzer.services.issue_analysis_service.AIClient')
    @patch('analyzer.services.issue_analysis_service.IssueProcessPipeline.process_issue_with_model_map')
    def test_worker_executes_pending_issue_process_task(self, mock_process_issue, mock_ai_cls, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {
                'server': 'http://jira.example.com',
                'username': 'tester',
                'password': 'secret',
                'field_name': 'CHERY_PROJECT',
            },
            'ai': {
                'base_url': 'http://llm.example.com',
                'api_key': 'demo',
                'model': 'Qwen3-32B-FP16',
                'pic_model': 'Qwen3-VL-8B',
            },
        }
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='PENDING',
        )

        def fake_process(issue, **kwargs):
            IssueProcessResult.objects.create(
                process_task=process_task,
                issue_key=process_task.issue_key,
                summary=process_task.summary,
                reply_text='分析完成',
                result_status='SUCCESS',
            )

        mock_jira_cls.return_value.search_issues.return_value = [object()]
        mock_process_issue.side_effect = fake_process

        call_command('run_task_worker', '--once')

        process_task.refresh_from_db()
        self.assertEqual(process_task.status, 'SUCCESS')
        self.assertEqual(process_task.progress, 100)
        self.assertTrue(IssueProcessResult.objects.filter(process_task=process_task).exists())
