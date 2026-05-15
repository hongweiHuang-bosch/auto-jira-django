from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from analyzer.models import (
    FilterTask,
    FilteredIssueSnapshot,
    IssueProcessResult,
    IssueProcessTask,
)
from analyzer.services.rule_group_payload import build_processed_issue_detail
from analyzer.services.rule_group_payload import build_processed_issue_page
from analyzer.services.rule_group_payload import build_rule_group_detail
from analyzer.services.rule_group_payload import build_rule_group_payload


class RuleGroupPayloadTests(TestCase):
    def setUp(self):
        self.filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            issue_count=1,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        self.snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=self.filter_task,
            issue_key='CHER-500',
            summary='主链路回归验证',
            assignee='alice',
        )

    def test_build_rule_group_detail_returns_stable_issue_action(self):
        process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='FAILED',
            stage='PARSING',
            progress=60,
        )
        IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            result_status='FAILED',
            reply_text='失败结果',
            error_message='解析失败',
        )

        payload = build_rule_group_detail(role_index=0, page=1, page_size=20)

        self.assertEqual(payload['group']['role_index'], 0)
        self.assertEqual(payload['filter_task']['id'], self.filter_task.id)
        self.assertEqual(payload['issues']['total'], 1)
        self.assertEqual(payload['issues']['items'][0]['latest_process_task']['id'], process_task.id)
        self.assertEqual(payload['issues']['items'][0]['next_action'], 'retry_process')

    def test_build_rule_group_payload_includes_config_name(self):
        payload = build_rule_group_payload()

        self.assertIn('name', payload[0])
        self.assertEqual(payload[0]['name'], payload[0]['role_label'])

    def test_build_rule_group_detail_uses_bounded_query_count(self):
        IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='SUCCESS',
            stage='SAVING_RESULT',
            progress=100,
        )

        with self.assertNumQueries(5):
            build_rule_group_detail(role_index=0, page=1, page_size=20)

    def test_build_processed_issue_page_returns_distinct_latest_processed_issues_for_role(self):
        older_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary='主链路回归验证',
            status='FAILED',
        )
        IssueProcessResult.objects.create(
            process_task=older_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text='旧处理结果',
        )
        latest_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary='主链路回归验证',
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=latest_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text='最新处理结果',
        )
        other_filter_task = FilterTask.objects.create(role_index=1, role_label='规则组 2', status='SUCCESS')
        other_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=other_filter_task,
            issue_key='OTHER-1',
            summary='其他规则组问题',
        )
        IssueProcessTask.objects.create(
            filter_task=other_filter_task,
            snapshot=other_snapshot,
            issue_key=other_snapshot.issue_key,
            summary=other_snapshot.summary,
            status='SUCCESS',
        )

        payload = build_processed_issue_page(role_index=0, page=1, page_size=20)

        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['items'][0]['issue_key'], 'CHER-500')
        self.assertEqual(payload['items'][0]['process_count'], 2)
        self.assertEqual(payload['items'][0]['latest_process_task']['id'], latest_task.id)
        self.assertEqual(payload['items'][0]['latest_result']['reply_text'], '最新处理结果')

    def test_build_processed_issue_page_supports_query_and_status_filters(self):
        failed_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary='主链路回归验证',
            status='FAILED',
        )
        IssueProcessResult.objects.create(
            process_task=failed_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            reply_text='失败处理结果',
        )
        success_snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=self.filter_task,
            issue_key='CHER-501',
            summary='蓝牙连接失败',
        )
        IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=success_snapshot,
            issue_key=success_snapshot.issue_key,
            summary=success_snapshot.summary,
            status='SUCCESS',
        )

        payload = build_processed_issue_page(role_index=0, page=1, page_size=20, query='主链路', status='FAILED')

        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['items'][0]['issue_key'], 'CHER-500')
        self.assertEqual(payload['items'][0]['latest_process_task']['status'], 'FAILED')

    def test_build_processed_issue_detail_returns_all_history_records_for_role_issue(self):
        older_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='FAILED',
            error_message='解析失败',
        )
        IssueProcessResult.objects.create(
            process_task=older_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            result_status='FAILED',
            reply_text='第一次处理正文',
        )
        latest_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=latest_task,
            issue_key=self.snapshot.issue_key,
            summary=self.snapshot.summary,
            result_status='SUCCESS',
            reply_text='第二次处理正文',
        )

        payload = build_processed_issue_detail(role_index=0, issue_key='CHER-500')

        self.assertEqual(payload['issue_key'], 'CHER-500')
        self.assertEqual(len(payload['records']), 2)
        self.assertEqual(payload['records'][0]['process_task']['id'], latest_task.id)
        self.assertEqual(payload['records'][0]['result']['reply_text'], '第二次处理正文')
        self.assertEqual(payload['records'][1]['result']['reply_text'], '第一次处理正文')

    @patch('analyzer.services.jira_issue_payload.load_config')
    def test_build_processed_issue_detail_includes_jira_browse_url(self, mock_load_config):
        mock_load_config.return_value = {'jira': {'server': 'https://jira.example.com/'}}
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
            result_status='SUCCESS',
            reply_text='处理正文',
        )

        payload = build_processed_issue_detail(role_index=0, issue_key='CHER-500')

        self.assertEqual(payload['jira_url'], 'https://jira.example.com/browse/CHER-500')
