from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from analyzer.models import (
    FilterTask,
    FilteredIssueSnapshot,
    IssueProcessResult,
    IssueProcessTask,
)
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
