from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from analyzer.models import FilterTask, FilteredIssueSnapshot, IssueProcessResult, IssueProcessTask, IssueReviewSample


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

    def test_create_issue_process_task_keeps_stale_running_task_as_conflict_until_worker_recovers(self):
        task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='RUNNING',
        )
        IssueProcessTask.objects.filter(pk=task.pk).update(
            updated_at=timezone.now() - timedelta(minutes=31)
        )

        response = self.client.post(
            f'/api/filter-tasks/{self.filter_task.id}/issues/{self.snapshot.issue_key}/process-tasks/',
            {},
            format='json',
        )

        task.refresh_from_db()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(task.status, 'RUNNING')

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

    def test_processed_issue_detail_includes_review_fields(self):
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text='分析结论',
        )

        response = self.client.get(
            f'/api/rule-groups/{self.filter_task.role_index}/processed-issues/{self.snapshot.issue_key}/'
        )

        self.assertEqual(response.status_code, 200)
        latest = response.data['records'][0]['result']
        self.assertEqual(latest['review_status'], 'PENDING')
        self.assertEqual(latest['review_reason'], '')
        self.assertEqual(latest['manual_override_after_review'], False)

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
            review_status='PASS',
        )

        response = self.client.post(f'/api/process-results/{result.id}/comment/')
        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertTrue(result.has_commented_to_jira)

    # ─── 辅助方法 ───────────────────────────────────────────────────

    def _create_process_result(self, reply_text='分析结论'):
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='SUCCESS',
        )
        return IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text=reply_text,
        )

    # ─── 任务 2：复核接口 ───────────────────────────────────────────

    @patch('analyzer.views.review_issue_result')
    def test_review_endpoint_marks_result_pass(self, mock_review_issue_result):
        mock_review_issue_result.return_value = {
            'review_status': 'PASS',
            'review_reason': '结论一致',
            'few_shot_count': 3,
            'review_model': 'Qwen3-32B-FP16',
        }
        result = self._create_process_result(reply_text='分析结论')

        response = self.client.post(f'/api/process-results/{result.id}/review/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertEqual(result.review_status, 'PASS')
        self.assertFalse(result.manual_override_after_review)

    @patch('analyzer.views.review_issue_result')
    def test_review_endpoint_marks_result_fail_and_creates_sample(self, mock_review_issue_result):
        mock_review_issue_result.return_value = {
            'review_status': 'FAIL',
            'review_reason': '评论与结论冲突',
            'few_shot_count': 2,
            'review_model': 'Qwen3-32B-FP16',
            'correct_conclusion': '建议人工检查 FLZCU 反馈链路',
        }
        result = self._create_process_result(reply_text='错误结论')

        response = self.client.post(f'/api/process-results/{result.id}/review/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertEqual(result.review_status, 'FAIL')
        self.assertEqual(IssueReviewSample.objects.count(), 1)

    @patch('analyzer.views.review_issue_result')
    def test_review_endpoint_uses_at_most_three_samples(self, mock_review_issue_result):
        mock_review_issue_result.return_value = {
            'review_status': 'PASS',
            'review_reason': '结论一致',
            'few_shot_count': 3,
            'review_model': 'Qwen3-32B-FP16',
        }
        for index in range(5):
            IssueReviewSample.objects.create(
                role_index=self.filter_task.role_index,
                issue_key=f'CHER-{index}',
                incorrect_conclusion=f'错误结论 {index}',
                correct_conclusion=f'正确结论 {index}',
                error_reason='历史错例',
            )
        result = self._create_process_result(reply_text='待复核结论')

        self.client.post(f'/api/process-results/{result.id}/review/', {}, format='json')

        args, _ = mock_review_issue_result.call_args
        self.assertEqual(len(args[1]), 3)

    # ─── 任务 3：保存回复与 Jira 回填闸门 ─────────────────────────

    def test_save_reply_after_fail_sets_manual_override_flag(self):
        result = self._create_process_result(reply_text='原结论')
        result.review_status = 'FAIL'
        result.save(update_fields=['review_status', 'updated_at'])

        response = self.client.patch(
            f'/api/process-results/{result.id}/',
            {'reply_text': '人工修正后的结论'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertEqual(result.review_status, 'PENDING')
        self.assertTrue(result.manual_override_after_review)

    @patch('analyzer.views.load_config')
    @patch('analyzer.views.JiraClient')
    def test_comment_requires_review_pass_or_manual_save_after_fail(self, mock_jira_cls, mock_load_config):
        mock_load_config.return_value = {
            'jira': {'server': 'http://jira.example.com', 'username': 'tester', 'password': 'secret'}
        }
        result = self._create_process_result(reply_text='原结论')
        result.review_status = 'FAIL'
        result.review_reason = '模型判断不可靠'
        result.save(update_fields=['review_status', 'review_reason', 'updated_at'])

        blocked = self.client.post(f'/api/process-results/{result.id}/comment/')
        self.assertEqual(blocked.status_code, 409)

        self.client.patch(
            f'/api/process-results/{result.id}/',
            {'reply_text': '人工修正后的结论'},
            format='json',
        )

        allowed = self.client.post(f'/api/process-results/{result.id}/comment/')
        self.assertEqual(allowed.status_code, 200)
