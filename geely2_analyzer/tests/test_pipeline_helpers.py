from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from geely2_analyzer.services.pipeline_helpers import (
    collect_bosch_signal_logs,
    select_latest_cycles,
)


class PipelineHelperTests(SimpleTestCase):
    def test_select_latest_cycles_returns_top_five_desc(self):
        cycle_paths = [Path(name) for name in ['cycle_1', 'cycle_12', 'cycle_7', 'cycle_9', 'cycle_4', 'cycle_11']]
        selected = select_latest_cycles(cycle_paths)
        self.assertEqual([path.name for path in selected], ['cycle_12', 'cycle_11', 'cycle_9', 'cycle_7', 'cycle_4'])

    def test_collect_bosch_signal_logs_groups_and_sorts_lines(self):
        with TemporaryDirectory() as tmp_dir:
            cycle_dir = Path(tmp_dir) / 'cycle_12'
            cycle_dir.mkdir(parents=True)
            log_file = cycle_dir / 'BoschVehicleHal.txt'
            log_file.write_text(
                '2026-04-21 10:00:02.000 BoschVehicleHal OTHER 0\n'
                '2026-04-21 10:00:01.000 BoschVehicleHal SIG_A 1\n'
                '2026-04-21 10:00:03.000 BoschVehicleHal SIG_A 0\n',
                encoding='utf-8',
            )

            grouped = collect_bosch_signal_logs([cycle_dir], ['SIG_A'])
            self.assertEqual(list(grouped.keys()), ['cycle_12'])
            self.assertEqual([item['line'] for item in grouped['cycle_12']], [
                '2026-04-21 10:00:01.000 BoschVehicleHal SIG_A 1',
                '2026-04-21 10:00:03.000 BoschVehicleHal SIG_A 0',
            ])
