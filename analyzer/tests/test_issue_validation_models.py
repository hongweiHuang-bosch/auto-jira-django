from django.db import IntegrityError
from django.test import TestCase

from analyzer.models import (
    FilterTask,
    FilteredIssueSnapshot,
    IssueProcessResult,
    IssueProcessTask,
    IssueValidationCheck,
    IssueValidationRun,
)


class IssueValidationModelTests(TestCase):
    def setUp(self):
        self.filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
        )
        self.snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=self.filter_task,
            issue_key='CHER-501',
            summary='校验测试',
            assignee='alice',
        )
        self.process_task = IssueProcessTask.objects.create(
            filter_task=self.filter_task,
            snapshot=self.snapshot,
            issue_key='CHER-501',
            summary='校验测试',
            status='SUCCESS',
        )
        self.result = IssueProcessResult.objects.create(
            process_task=self.process_task,
            issue_key='CHER-501',
            summary='校验测试',
            reply_text='AI 结论',
        )

    def test_validation_run_defaults_to_pending_without_manual_override(self):
        run = IssueValidationRun.objects.create(process_result=self.result)
        self.assertEqual(run.status, 'PENDING')
        self.assertEqual(run.system_verdict, 'UNKNOWN')
        self.assertEqual(run.manual_verdict, '')

    def test_validation_check_is_unique_per_run_and_type(self):
        run = IssueValidationRun.objects.create(process_result=self.result)
        IssueValidationCheck.objects.create(
            validation_run=run,
            check_type='AI_RESULT_VS_CANTRACE',
            status='FAIL',
            title='AI 与 cantrace',
            reason='时间不匹配',
            sort_order=10,
        )
        with self.assertRaises(IntegrityError):
            IssueValidationCheck.objects.create(
                validation_run=run,
                check_type='AI_RESULT_VS_CANTRACE',
                status='FAIL',
                title='重复检查项',
                reason='重复',
                sort_order=20,
            )
