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
        self.assertEqual(payload['table_rows'], [])
        self.assertEqual(payload['checks'][0]['evidence_payload']['table_rows'], [])

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
        self.assertEqual(payload['checks'][0]['evidence_payload']['table_rows'], payload['table_rows'])
        self.assertEqual(payload['table_rows'][0]['status'], 'FAIL')
        self.assertEqual(payload['chart_payload']['series'][0]['points'][0]['at'], '12:01:08')

    def test_matching_signal_time_passes_with_chart_and_evidence_rows(self):
        payload = build_validation_payload(
            reply_text='AI 判断 BCM_DriverDoorAjar 在 12:01:05 从 0 到 1',
            cantrace_payload={
                'signals': [
                    {
                        'name': 'BCM_DriverDoorAjar',
                        'at': '12:01:05',
                        'from': '0',
                        'to': '1',
                    }
                ]
            },
            upper_requirement_text='门打开后 BCM_DriverDoorAjar 变为 1',
        )

        self.assertEqual(payload['system_verdict'], 'PASS')
        self.assertIn('时间点一致', payload['summary_reason'])
        self.assertEqual(payload['checks'][0]['status'], 'PASS')
        self.assertEqual(payload['table_rows'][0]['status'], 'PASS')
        self.assertEqual(payload['checks'][0]['evidence_payload']['table_rows'], payload['table_rows'])
        self.assertEqual(payload['checks'][0]['evidence_payload']['chart_payload'], payload['chart_payload'])

    def test_multiple_signals_are_all_rendered_and_any_mismatch_fails(self):
        payload = build_validation_payload(
            reply_text='AI 判断 BCM_DriverDoorAjar 在 12:01:05 从 0 到 1',
            cantrace_payload={
                'signals': [
                    {'name': 'BCM_DriverDoorAjar', 'at': '12:01:05', 'from': '0', 'to': '1'},
                    {'name': 'BCM_PassengerDoorAjar', 'at': '12:01:08', 'from': '0', 'to': '1'},
                ]
            },
            upper_requirement_text='门打开后车门信号变为 1',
        )

        self.assertEqual(payload['system_verdict'], 'FAIL')
        self.assertEqual(len(payload['table_rows']), 2)
        self.assertEqual(len(payload['chart_payload']['series']), 2)
        self.assertEqual(payload['table_rows'][0]['status'], 'PASS')
        self.assertEqual(payload['table_rows'][1]['status'], 'FAIL')
        self.assertIn('时间点不匹配', payload['summary_reason'])

    def test_signal_missing_at_fails_and_is_rendered(self):
        payload = build_validation_payload(
            reply_text='AI 判断 BCM_DriverDoorAjar 在 12:01:05 从 0 到 1',
            cantrace_payload={
                'signals': [
                    {'name': 'BCM_DriverDoorAjar', 'from': '0', 'to': '1'},
                ]
            },
            upper_requirement_text='门打开后 BCM_DriverDoorAjar 变为 1',
        )

        self.assertEqual(payload['system_verdict'], 'FAIL')
        self.assertIn('缺少信号时间点', payload['summary_reason'])
        self.assertEqual(payload['table_rows'][0]['status'], 'FAIL')
        self.assertEqual(payload['table_rows'][0]['cantrace_time'], '')
        self.assertEqual(payload['checks'][0]['evidence_payload']['table_rows'], payload['table_rows'])
