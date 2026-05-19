from django.test import SimpleTestCase

from analyzer.services.issue_validation_service import build_validation_payload


class IssueValidationServiceTests(SimpleTestCase):
    def test_missing_cantrace_becomes_unknown_summary(self):
        payload = build_validation_payload(
            reply_text='AI 判断 12:01:05 门开',
            cantrace_payload=None,
            upper_requirement_text='门打开后信号置 1',
        )
        self.assertEqual(payload['system_verdict'], 'UNKNOWN')
        self.assertIn('缺少可用 cantrace 数据', payload['summary_reason'])

    def test_signal_mismatch_creates_fail_check_and_table_row(self):
        payload = build_validation_payload(
            reply_text='AI 判断 BCM_DriverDoorAjar 在 12:01:05 从 0 到 1',
            cantrace_payload={
                'signals': [
                    {
                        'name': 'BCM_DriverDoorAjar',
                        'at': '12:01:08',
                        'from': '0',
                        'to': '1',
                    }
                ]
            },
            upper_requirement_text='门打开后 BCM_DriverDoorAjar 变为 1',
        )
        self.assertEqual(payload['system_verdict'], 'FAIL')
        self.assertEqual(payload['checks'][0]['check_type'], 'AI_RESULT_VS_CANTRACE')
        self.assertTrue(payload['table_rows'])
