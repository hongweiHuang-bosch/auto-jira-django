from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from analyzer.models import (
    FilterTask,
    FilteredIssueSnapshot,
    IssueProcessResult,
    IssueProcessTask,
)


class FilterTaskApiTests(APITestCase):
    @patch('analyzer.views.submit_filter_task')
    def test_create_filter_task(self, mock_submit_filter_task):
        response = self.client.post('/api/rule-groups/0/filter-tasks/', {'force_refresh': True}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FilterTask.objects.count(), 1)
        mock_submit_filter_task.assert_called_once_with(FilterTask.objects.get().id)

    def test_rule_group_list_returns_latest_filter_summary(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=2,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-1',
            summary='黑屏问题',
            assignee='alice',
        )

        response = self.client.get('/api/rule-groups/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['latest_filter_task']['issue_count'], 2)

    def test_latest_filter_task_endpoint_returns_issue_page(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=1,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-2',
            summary='花屏问题',
            assignee='bob',
        )

        response = self.client.get('/api/rule-groups/0/filter-tasks/latest/?include_issues=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['filter_task']['id'], task.id)
        self.assertEqual(len(response.data['issues']['items']), 1)

    def test_filter_task_issue_list_endpoint_returns_snapshot_items(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=1,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-3',
            summary='蓝屏问题',
            assignee='carol',
        )

        response = self.client.get(f'/api/filter-tasks/{task.id}/issues/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['items'][0]['issue_key'], 'CHER-3')

    def test_rule_group_detail_endpoint_returns_stable_payload(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=1,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-4',
            summary='倒车影像黑屏',
            assignee='dave',
        )
        process_task = IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
            stage='SAVING_RESULT',
            progress=100,
        )
        IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            result_status='SUCCESS',
            reply_text='分析完成',
        )

        response = self.client.get('/api/rule-groups/0/detail/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['group']['role_index'], 0)
        self.assertEqual(response.data['issues']['items'][0]['next_action'], 'view_result')

    def test_processed_issue_list_endpoint_supports_search_and_status_filter(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=2,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-21',
            summary='倒车影像黑屏',
            assignee='alice',
        )
        process_task = IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            reply_text='历史处理正文',
        )
        failed_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-22',
            summary='蓝牙连接失败',
        )
        IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=failed_snapshot,
            issue_key=failed_snapshot.issue_key,
            summary=failed_snapshot.summary,
            status='FAILED',
        )

        response = self.client.get('/api/rule-groups/0/processed-issues/?q=倒车&status=SUCCESS')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['items'][0]['issue_key'], 'CHER-21')
        self.assertEqual(response.data['items'][0]['latest_result']['reply_text'], '历史处理正文')

    def test_processed_issue_detail_endpoint_returns_history_records(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-23',
            summary='座舱重启',
        )
        process_task = IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            reply_text='单票历史正文',
        )

        response = self.client.get('/api/rule-groups/0/processed-issues/CHER-23/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['issue_key'], 'CHER-23')
        self.assertEqual(response.data['records'][0]['result']['reply_text'], '单票历史正文')

    @patch('analyzer.services.jira_issue_payload.load_config')
    @patch('analyzer.services.jira_issue_payload.JiraClient')
    def test_processed_issue_jira_endpoint_returns_comments_transitions_and_candidates(self, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {
                'server': 'https://jira.example.com/',
                'username': 'tester',
                'password': 'secret',
            }
        }
        task = FilterTask.objects.create(role_index=0, role_label='规则组 1', status='SUCCESS')
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-24',
            summary='座舱重启',
            assignee='Alice',
        )
        IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )
        mock_jira = mock_jira_cls.return_value
        mock_jira.get_issue.return_value = SimpleNamespace(
            fields=SimpleNamespace(
                assignee=SimpleNamespace(accountId='alice-id', name='alice', displayName='Alice'),
                reporter=SimpleNamespace(accountId='bob-id', name='bob', displayName='Bob'),
            )
        )
        mock_jira.get_comments.return_value = [
            {
                'author': {'account_id': 'carol-id', 'name': 'carol', 'display_name': 'Carol'},
                'body': '请转给 Carol 继续分析',
                'created': '2026-05-01T10:00:00.000+0800',
                'updated': '2026-05-01T10:00:00.000+0800',
            }
        ]
        mock_jira.get_transitions.return_value = [{'id': '31', 'name': '转处理中'}]

        response = self.client.get('/api/rule-groups/0/processed-issues/CHER-24/jira/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['jira_url'], 'https://jira.example.com/browse/CHER-24')
        self.assertEqual(response.data['comments'][0]['body'], '请转给 Carol 继续分析')
        self.assertEqual(response.data['transition_candidates'][0]['id'], '31')
        self.assertEqual(
            [item['display_name'] for item in response.data['user_candidates']],
            ['Alice', 'Bob', 'Carol'],
        )

    @patch('analyzer.services.jira_issue_payload.load_config')
    @patch('analyzer.services.jira_issue_payload.JiraClient')
    def test_processed_issue_jira_endpoint_reports_jira_errors_without_history_failure(self, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {
                'server': 'https://jira.example.com/',
                'username': 'tester',
                'password': 'secret',
            }
        }
        task = FilterTask.objects.create(role_index=0, role_label='规则组 1', status='SUCCESS')
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-25',
            summary='座舱重启',
        )
        IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )
        mock_jira_cls.return_value.get_issue.side_effect = RuntimeError('jira timeout')

        response = self.client.get('/api/rule-groups/0/processed-issues/CHER-25/jira/')

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data['detail'], 'Jira 信息加载失败')
        self.assertNotIn('secret', str(response.data))

    def test_processed_issue_transition_endpoint_validates_required_fields(self):
        task = FilterTask.objects.create(role_index=0, role_label='规则组 1', status='SUCCESS')
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-26',
            summary='座舱重启',
        )
        IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )

        response = self.client.post('/api/rule-groups/0/processed-issues/CHER-26/transition/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], '缺少 transition_id 或 target_user')

    @patch('analyzer.services.jira_issue_payload.load_config')
    @patch('analyzer.services.jira_issue_payload.JiraClient')
    def test_processed_issue_transition_endpoint_assigns_and_transitions_issue(self, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {
                'server': 'https://jira.example.com/',
                'username': 'tester',
                'password': 'secret',
            }
        }
        task = FilterTask.objects.create(role_index=0, role_label='规则组 1', status='SUCCESS')
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=task,
            issue_key='CHER-27',
            summary='座舱重启',
        )
        IssueProcessTask.objects.create(
            filter_task=task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )

        response = self.client.post(
            '/api/rule-groups/0/processed-issues/CHER-27/transition/',
            {'transition_id': '31', 'target_user': 'alice-id'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['detail'], '流转成功')
        mock_jira_cls.return_value.assign_issue.assert_called_once_with('CHER-27', 'alice-id')
        mock_jira_cls.return_value.transition_issue.assert_called_once_with('CHER-27', '31')
