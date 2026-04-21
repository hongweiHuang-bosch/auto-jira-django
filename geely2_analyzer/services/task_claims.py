from django.db import transaction
from django.utils import timezone

from geely2_analyzer.models import Geely2AnalysisTask, Geely2SyncTask


def claim_pending_sync_task():
    with transaction.atomic():
        task = (
            Geely2SyncTask.objects
            .select_for_update(skip_locked=True)
            .filter(status='PENDING')
            .order_by('created_at')
            .first()
        )
        if task is None:
            return None
        task.status = 'RUNNING'
        task.started_at = timezone.now()
        task.message = '同步任务执行中'
        task.save(update_fields=['status', 'started_at', 'message', 'updated_at'])
        return task.pk


def claim_pending_analysis_task():
    with transaction.atomic():
        task = (
            Geely2AnalysisTask.objects
            .select_for_update(skip_locked=True)
            .filter(status='PENDING')
            .order_by('created_at')
            .first()
        )
        if task is None:
            return None
        task.status = 'RUNNING'
        task.started_at = timezone.now()
        task.message = '分析任务执行中'
        task.save(update_fields=['status', 'started_at', 'message', 'updated_at'])
        return task.pk
