import time

from django.core.management.base import BaseCommand

from analyzer.models import IssueProcessTask
from analyzer.services.filter_task_runner import claim_pending_filter_task, run_filter_task
from analyzer.services.issue_analysis_service import run_issue_process_task


def claim_pending_issue_process_task():
    task = IssueProcessTask.objects.filter(status='PENDING').order_by('created_at').first()
    return task.id if task else None


class Command(BaseCommand):
    help = '执行筛票任务和单票处理任务的最小 Worker。'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--poll-interval', type=float, default=2.0)

    def handle(self, *args, **options):
        if options['once']:
            filter_task_id = claim_pending_filter_task()
            if filter_task_id is not None:
                run_filter_task(filter_task_id)
                return

            process_task_id = claim_pending_issue_process_task()
            if process_task_id is not None:
                run_issue_process_task(process_task_id)
            return

        while True:
            filter_task_id = claim_pending_filter_task()
            if filter_task_id is not None:
                run_filter_task(filter_task_id)
            else:
                process_task_id = claim_pending_issue_process_task()
                if process_task_id is not None:
                    run_issue_process_task(process_task_id)
            time.sleep(options['poll_interval'])
