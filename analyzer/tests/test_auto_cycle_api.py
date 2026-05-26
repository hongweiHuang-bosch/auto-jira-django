from django.utils import timezone
from rest_framework.test import APITestCase

from analyzer.models import AutoCycleState, FilterTask, FilteredIssueSnapshot, IssueProcessTask


class AutoCycleApiTests(APITestCase):
    def test_get_auto_cycle_returns_default_stopped_state(self):
        response = self.client.get('/api/auto-cycle/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_running'])
        self.assertEqual(response.data['interval_minutes'], 30)
        self.assertEqual(response.data['stage'], 'STOPPED')

    def test_start_auto_cycle_uses_interval_minutes(self):
        response = self.client.post('/api/auto-cycle/start/', {'interval_minutes': 15}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_running'])
        self.assertEqual(response.data['interval_minutes'], 15)
        self.assertEqual(response.data['stage'], 'IDLE')
        self.assertFalse(response.data['stop_requested'])
        self.assertIsNotNone(response.data['next_run_at'])

    def test_start_auto_cycle_rejects_non_positive_interval(self):
        response = self.client.post('/api/auto-cycle/start/', {'interval_minutes': 0}, format='json')

        self.assertEqual(response.status_code, 400)

    def test_stop_auto_cycle_marks_running_process_tasks_failed(self):
        state = AutoCycleState.objects.create(
            is_running=True,
            interval_minutes=10,
            stage='PROCESSING',
            stop_requested=False,
        )
        filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            expires_at=timezone.now(),
        )
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-1',
            summary='测试票',
        )
        running_task = IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='RUNNING',
        )

        response = self.client.post('/api/auto-cycle/stop/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        state.refresh_from_db()
        running_task.refresh_from_db()
        self.assertFalse(state.is_running)
        self.assertTrue(state.stop_requested)
        self.assertEqual(state.stage, 'STOPPED')
        self.assertEqual(running_task.status, 'FAILED')
        self.assertIn('用户停止周期任务', running_task.error_message)