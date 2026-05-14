from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from analyzer.models import FilterTask, FilteredIssueSnapshot


class FilterTaskWorkerTests(TestCase):
    @patch('analyzer.services.filter_task_runner.load_config')
    @patch('analyzer.services.filter_task_runner.JiraClient')
    def test_worker_executes_pending_filter_task(self, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {
                'server': 'http://jira.example.com',
                'username': 'tester',
                'password': 'secret',
                'use_system_proxy': False,
                'proxies': None,
            }
        }
        mock_jira_cls.return_value.search_issues.return_value = [
            SimpleNamespace(
                key='CHER-100',
                fields=SimpleNamespace(
                    summary='黑屏问题',
                    assignee=SimpleNamespace(displayName='alice'),
                    updated='2026-04-20T10:00:00.000+0800',
                ),
            )
        ]

        FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='PENDING',
        )

        call_command('run_task_worker', '--once')

        mock_jira_cls.assert_called_once_with(
            server='http://jira.example.com',
            username='tester',
            password='secret',
            use_system_proxy=False,
            proxies=None,
        )

        task = FilterTask.objects.get()
        self.assertEqual(task.status, 'SUCCESS')
        self.assertEqual(task.issue_count, 1)
        self.assertGreater(task.expires_at, timezone.now() + timedelta(hours=23))
        self.assertEqual(FilteredIssueSnapshot.objects.count(), 1)
        self.assertEqual(FilteredIssueSnapshot.objects.get().issue_key, 'CHER-100')
