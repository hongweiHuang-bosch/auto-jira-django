from pathlib import Path
from tempfile import NamedTemporaryFile

from django.test import SimpleTestCase

from legacy_core.can_trace import _parse_trace_with_retry


class CanTraceAscParsingTests(SimpleTestCase):
    def test_parse_trace_with_retry_accepts_canfd_lines_with_can_id_before_direction(self):
        content = """date Thu May 14 03:49:01 PM 2026
base hex timestamps absolute
// version 7.0.0
    internal events logged
0.000000 CANFD 1 414 Tx 0 0 d 8 8 00 00 00 00 00 00 00 08
"""

        with NamedTemporaryFile('w', suffix='.asc', delete=False, encoding='utf-8') as handle:
            handle.write(content)
            asc_path = Path(handle.name)

        self.addCleanup(lambda: asc_path.unlink(missing_ok=True))

        trace_data, start_time = _parse_trace_with_retry({}, {}, str(asc_path), None)

        self.assertEqual(trace_data, {})
        self.assertGreater(start_time, 0)