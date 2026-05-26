from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from analyzer.models import AutoCycleState, FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask
from analyzer.services.auto_cycle_service import notify_finished_process_tasks, run_auto_cycle_once


class AutoCycleServiceTests(TestCase):
    @patch(
        'analyzer.services.task_catalog._get_map_car_role',
        return_value=({'name': '规则组 1', 'jql': 'project = CHER'},),
    )
    @patch('analyzer.services.auto_cycle_service.submit_filter_task')
    def test_run_auto_cycle_once_creates_due_filter_tasks(self, mock_submit_filter_task, _mock_map_car_role):
        AutoCycleState.objects.create(
            is_running=True,
            interval_minutes=5,
            stage='IDLE',
            next_run_at=timezone.now() - timedelta(seconds=1),
        )

        state = run_auto_cycle_once()

        self.assertEqual(state.stage, 'IDLE')
        self.assertGreater(state.next_run_at, timezone.now())
        self.assertTrue(FilterTask.objects.filter(role_index=0, status='PENDING').exists())
        mock_submit_filter_task.assert_called_once()

    @patch(
        'analyzer.services.task_catalog._get_map_car_role',
        return_value=({'name': '规则组 1', 'jql': 'project = CHER'},),
    )
    def test_run_auto_cycle_once_creates_process_tasks_for_unprocessed_snapshots(self, _mock_map_car_role):
        AutoCycleState.objects.create(
            is_running=True,
            interval_minutes=5,
            stage='IDLE',
            next_run_at=timezone.now() + timedelta(minutes=3),
        )
        filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=2,
        )
        first_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-1',
            summary='新票',
        )
        processed_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-2',
            summary='已处理票',
        )
        IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=processed_snapshot,
            issue_key=processed_snapshot.issue_key,
            summary=processed_snapshot.summary,
            status='SUCCESS',
        )

        run_auto_cycle_once()

        self.assertTrue(IssueProcessTask.objects.filter(snapshot=first_snapshot, status='PENDING').exists())
        self.assertEqual(IssueProcessTask.objects.filter(snapshot=processed_snapshot).count(), 1)

    @patch('analyzer.services.auto_cycle_service.send_feishu_post_message')
    def test_notify_finished_process_tasks_sends_success_and_failure_once(self, mock_send_feishu_post_message):
        filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
        )
        success_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-1',
            summary='成功票',
        )
        success_task = IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=success_snapshot,
            issue_key=success_snapshot.issue_key,
            summary=success_snapshot.summary,
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=success_task,
            issue_key=success_task.issue_key,
            summary=success_task.summary,
            reply_text='分析结果',
            upper_comment='jira描述和上层评论',
        )
        failed_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-2',
            summary='失败票',
        )
        failed_task = IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=failed_snapshot,
            issue_key=failed_snapshot.issue_key,
            summary=failed_snapshot.summary,
            status='FAILED',
            error_message='处理失败',
        )

        self.assertEqual(notify_finished_process_tasks(), 2)
        self.assertEqual(notify_finished_process_tasks(), 0)
        self.assertEqual(mock_send_feishu_post_message.call_count, 2)
        success_paragraphs = mock_send_feishu_post_message.call_args_list[0][0][1]
        self.assertIn('jira描述和上层评论', success_paragraphs[3][0]['text'])
        self.assertIn('分析结果', success_paragraphs[4][0]['text'])
        success_task.refresh_from_db()
        failed_task.refresh_from_db()
        self.assertIsNotNone(success_task.feishu_notified_at)
        self.assertIsNotNone(failed_task.feishu_notified_at)