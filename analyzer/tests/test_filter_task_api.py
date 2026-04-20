from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from analyzer.models import FilterTask, FilteredIssueSnapshot


class FilterTaskApiTests(APITestCase):
    def test_create_filter_task(self):
        response = self.client.post('/api/rule-groups/0/filter-tasks/', {'force_refresh': True}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FilterTask.objects.count(), 1)

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
