from datetime import timedelta
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
