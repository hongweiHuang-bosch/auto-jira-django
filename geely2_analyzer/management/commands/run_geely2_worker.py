import time

from django.core.management.base import BaseCommand

from geely2_analyzer.services.sync_runner import run_sync_task
from geely2_analyzer.services.task_claims import (
    claim_pending_analysis_task,
    claim_pending_sync_task,
)


class Command(BaseCommand):
    help = '执行 Geely2 同步和分析任务的 Worker。'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--poll-interval', type=float, default=2.0)

    def _run_once(self):
        sync_task_id = claim_pending_sync_task()
        if sync_task_id is not None:
            run_sync_task(sync_task_id)
            return

        analysis_task_id = claim_pending_analysis_task()
        if analysis_task_id is not None:
            from geely2_analyzer.services.analysis_runner import run_analysis_task
            run_analysis_task(analysis_task_id)

    def handle(self, *args, **options):
        if options['once']:
            self._run_once()
            return
        while True:
            self._run_once()
            time.sleep(options['poll_interval'])
