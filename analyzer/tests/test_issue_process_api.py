from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask


class IssueProcessApiTests(APITestCase):
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
            issue_key='CHER-200',
            summary='倒车影像异常',
            assignee='alice',
        )

    def test_create_issue_process_task(self):
        response = self.client.post(
            f'/api/filter-tasks/{self.filter_task.id}/issues/{self.snapshot.issue_key}/process-tasks/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(IssueProcessTask.objects.count(), 1)

    def test_create_issue_process_task_conflicts_when_active_task_exists(self):
        IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='RUNNING',
        )
        response = self.client.post(
            f'/api/filter-tasks/{self.filter_task.id}/issues/{self.snapshot.issue_key}/process-tasks/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 409)

    def test_get_issue_process_task_detail(self):
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='RUNNING',
            stage='PARSING',
            progress=45,
        )
        response = self.client.get(f'/api/process-tasks/{process_task.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stage'], 'PARSING')

    def test_patch_issue_process_result(self):
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='SUCCESS',
        )
        result = IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text='旧内容',
        )
        response = self.client.patch(
            f'/api/process-results/{result.id}/',
            {'reply_text': '新内容'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertEqual(result.reply_text, '新内容')

    @patch('analyzer.views.load_config')
    @patch('analyzer.views.JiraClient')
    def test_comment_issue_process_result(self, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {
                'server': 'http://jira.example.com',
                'username': 'tester',
                'password': 'secret',
            }
        }
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='SUCCESS',
        )
        result = IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text='分析结论',
        )

        response = self.client.post(f'/api/process-results/{result.id}/comment/')
        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertTrue(result.has_commented_to_jira)
