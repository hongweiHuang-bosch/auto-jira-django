import json

from django.test import SimpleTestCase

from analyzer.services.cantrace_payload import build_raw_signals_json, parse_cantrace_summary


class CantracePayloadTests(SimpleTestCase):
    def test_build_raw_signals_json_from_cantrace_summary(self):
        raw_signals = build_raw_signals_json(
            'ICC_SetCLMOn值为 2 持续了 4 帧，从时间 2026-05-19 17:23:58.778 到 2026-05-19 17:23:58.905\n'
            'ICC_SetCLMOn值为 0 持续了 46 帧，从时间 2026-05-19 17:23:58.913 到 2026-05-19 17:24:03.305'
        )

        payload = json.loads(raw_signals)
        self.assertEqual(payload['signals'][0]['name'], 'ICC_SetCLMOn')
        self.assertEqual(payload['signals'][0]['to'], '2')
        self.assertEqual(payload['signals'][0]['at'], '17:23:58')
        self.assertEqual(len(payload['signals']), 2)

    def test_parse_cantrace_summary_ignores_unmatched_lines(self):
        signals = parse_cantrace_summary(
            'not a cantrace line\n'
            'ICC_PM25Switch值为 0 持续了 1220 帧，从时间 2026-05-14 15:31:05.560 到结束'
        )

        self.assertEqual(signals, [
            {'name': 'ICC_PM25Switch', 'at': '15:31:05', 'from': '', 'to': '0'},
        ])

    def test_build_raw_signals_json_returns_empty_for_missing_signals(self):
        self.assertEqual(build_raw_signals_json(''), '')
        self.assertEqual(build_raw_signals_json('not a cantrace line'), '')
