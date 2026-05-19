from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from analyzer.models import (
    FilterTask,
    FilteredIssueSnapshot,
    IssueProcessResult,
    IssueProcessTask,
    IssueValidationCheck,
    IssueValidationRun,
)
from analyzer.services.issue_validation_runner import run_issue_validation_run
from analyzer.services.task_claims import claim_pending_issue_validation_run


class IssueValidationApiTests(APITestCase):
    def _create_process_result(self, **result_kwargs):
        filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
        )
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-700',
            summary='校验测试',
            assignee='alice',
        )
        process_task = IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='SUCCESS',
        )
        defaults = {
            'process_task': process_task,
            'issue_key': snapshot.issue_key,
            'summary': snapshot.summary,
            'reply_text': 'AI 判断 BCM_DriverDoorAjar 在 12:01:05 从 0 到 1',
        }
        defaults.update(result_kwargs)
        return IssueProcessResult.objects.create(**defaults)

    def test_create_validation_run(self):
        result = self._create_process_result()

        response = self.client.post(f'/api/process-results/{result.id}/validation-runs/', {}, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(IssueValidationRun.objects.count(), 1)
        run = IssueValidationRun.objects.get()
        self.assertEqual(response.data['validation_run_id'], run.id)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertEqual(run.process_result, result)

    def test_latest_validation_run_returns_404_when_missing(self):
        result = self._create_process_result()

        response = self.client.get(f'/api/process-results/{result.id}/validation-runs/latest/')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['detail'], '暂无校验记录')

    def test_latest_validation_run_returns_latest_run(self):
        result = self._create_process_result()
        older = IssueValidationRun.objects.create(process_result=result, status='SUCCESS')
        latest = IssueValidationRun.objects.create(process_result=result, status='FAILED')
        IssueValidationRun.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timezone.timedelta(minutes=5)
        )

        response = self.client.get(f'/api/process-results/{result.id}/validation-runs/latest/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], latest.id)
        self.assertEqual(response.data['status'], 'FAILED')

    def test_validation_run_detail_includes_checks(self):
        result = self._create_process_result()
        run = IssueValidationRun.objects.create(process_result=result, status='SUCCESS')
        IssueValidationCheck.objects.create(
            validation_run=run,
            check_type='AI_RESULT_VS_CANTRACE',
            status='PASS',
            title='AI 结果 vs cantrace 一致性',
            reason='一致',
            sort_order=10,
        )

        response = self.client.get(f'/api/validation-runs/{run.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], run.id)
        self.assertEqual(len(response.data['checks']), 1)
        self.assertEqual(response.data['checks'][0]['check_type'], 'AI_RESULT_VS_CANTRACE')

    def test_save_manual_override_validates_saved_fields_and_anonymous_operator(self):
        result = self._create_process_result()
        run = IssueValidationRun.objects.create(process_result=result, status='SUCCESS')

        response = self.client.patch(
            f'/api/validation-runs/{run.id}/override/',
            {
                'manual_verdict': 'WARNING',
                'manual_reason': '  需要人工关注  ',
                'manual_note': '  cantrace 证据不足  ',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        run.refresh_from_db()
        self.assertEqual(run.manual_verdict, 'WARNING')
        self.assertEqual(run.manual_reason, '需要人工关注')
        self.assertEqual(run.manual_note, 'cantrace 证据不足')
        self.assertEqual(run.manual_operator, 'anonymous')
        self.assertIsNotNone(run.manual_saved_at)
        self.assertEqual(response.data['manual_operator'], 'anonymous')

    def test_manual_override_rejects_blank_reason_or_note(self):
        result = self._create_process_result()
        run = IssueValidationRun.objects.create(process_result=result, status='SUCCESS')
        url = f'/api/validation-runs/{run.id}/override/'

        reason_response = self.client.patch(
            url,
            {'manual_verdict': 'PASS', 'manual_reason': ' ', 'manual_note': '人工确认'},
            format='json',
        )
        note_response = self.client.patch(
            url,
            {'manual_verdict': 'PASS', 'manual_reason': '人工确认', 'manual_note': ''},
            format='json',
        )

        self.assertEqual(reason_response.status_code, 400)
        self.assertEqual(note_response.status_code, 400)

    def test_worker_claim_and_runner_persists_success_payload(self):
        result = self._create_process_result(raw_signals='BCM_DriverDoorAjar')
        run = IssueValidationRun.objects.create(process_result=result, status='PENDING')

        claimed_id = claim_pending_issue_validation_run()
        self.assertEqual(claimed_id, run.id)
        run.refresh_from_db()
        self.assertEqual(run.status, 'RUNNING')
        self.assertIsNotNone(run.started_at)

        run_issue_validation_run(claimed_id)

        run.refresh_from_db()
        self.assertEqual(run.status, 'SUCCESS')
        self.assertEqual(run.system_verdict, 'FAIL')
        self.assertTrue(run.summary_reason)
        self.assertIn('table_rows', run.evidence_payload)
        self.assertIn('series', run.chart_payload)
        self.assertIsNotNone(run.finished_at)
        self.assertEqual(run.checks.count(), 1)
        check = run.checks.get()
        self.assertEqual(check.check_type, 'AI_RESULT_VS_CANTRACE')
        self.assertTrue(check.evidence_payload)

    def test_runner_marks_failed_when_validation_service_raises(self):
        result = self._create_process_result()
        run = IssueValidationRun.objects.create(process_result=result, status='RUNNING')

        with patch(
            'analyzer.services.issue_validation_runner.build_validation_payload',
            side_effect=ValueError('validation exploded'),
        ):
            run_issue_validation_run(run.id)

        run.refresh_from_db()
        self.assertEqual(run.status, 'FAILED')
        self.assertEqual(run.error_message, 'validation exploded')
        self.assertIsNotNone(run.finished_at)
