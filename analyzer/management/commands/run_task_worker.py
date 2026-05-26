import time

from django.core.management.base import BaseCommand

from analyzer.services.filter_task_runner import run_filter_task
from analyzer.services.auto_cycle_service import run_auto_cycle_once, notify_finished_process_tasks
from analyzer.services.issue_analysis_service import run_issue_process_task
from analyzer.services.issue_validation_runner import run_issue_validation_run
from analyzer.services.task_claims import (
    claim_pending_filter_task,
    claim_pending_issue_process_task,
    claim_pending_issue_validation_run,
    recover_stale_issue_process_tasks,
    recover_stale_issue_validation_runs,
)
from legacy_core.utils import setup_logging


class Command(BaseCommand):
    help = '执行筛票任务和单票处理任务的最小 Worker。'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--poll-interval', type=float, default=2.0)

    def _run_once(self):
        recover_stale_issue_process_tasks(timeout_minutes=30)
        recover_stale_issue_validation_runs(timeout_minutes=30)
        notify_finished_process_tasks()
        run_auto_cycle_once()

        filter_task_id = claim_pending_filter_task()
        if filter_task_id is not None:
            run_filter_task(filter_task_id)
            return

        process_task_id = claim_pending_issue_process_task()
        if process_task_id is not None:
            run_issue_process_task(process_task_id)
            return

        validation_run_id = claim_pending_issue_validation_run()
        if validation_run_id is not None:
            run_issue_validation_run(validation_run_id)

    def handle(self, *args, **options):
        setup_logging()

        if options['once']:
            self._run_once()
            return

        while True:
            self._run_once()
            time.sleep(options['poll_interval'])
