from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.utils import timezone

from analyzer.models import IssueProcessResult, IssueProcessTask
from analyzer.services.rule_group_stream import publish_rule_group_snapshot


def create_issue_process_pipeline(*args, process_task_id: int, **kwargs):
    """Lazy factory to avoid importing Pipeline (and its ML deps) at module load time."""
    from legacy_core.pipeline import Pipeline

    class _IssueProcessPipeline(Pipeline):
        def __init__(self, *a, process_task_id: int, **kw):
            super().__init__(*a, **kw)
            self.process_task_id = process_task_id

        def save_true_or_false(self, issue_key):
            return None

        def _to_media_url(self, file_path: str) -> str:
            if not file_path:
                return ''
            try:
                path = Path(file_path).resolve()
                media_root = Path(settings.MEDIA_ROOT).resolve()
                rel = path.relative_to(media_root)
                return settings.MEDIA_URL.rstrip('/') + '/' + str(rel).replace('\\', '/')
            except Exception:
                return ''

        def _error_proces(self, issue_key: str, summary: str, reply_text: str):
            process_task = IssueProcessTask.objects.get(pk=self.process_task_id)
            process_task.status = 'FAILED'
            process_task.error_message = reply_text
            process_task.finished_at = timezone.now()
            process_task.save(update_fields=['status', 'error_message', 'finished_at', 'updated_at'])
            IssueProcessResult.objects.update_or_create(
                process_task=process_task,
                defaults={
                    'issue_key': issue_key,
                    'summary': summary,
                    'result_status': 'MANUAL',
                    'reply_text': reply_text,
                    'error_message': reply_text,
                },
            )
            publish_rule_group_snapshot()

        def _finalize_issue(self, issue_key: str, summary: str, reply_text: str, can_img_path: str):
            process_task = IssueProcessTask.objects.get(pk=self.process_task_id)
            process_task.status = 'SUCCESS'
            process_task.progress = 100
            process_task.stage = 'SAVING_RESULT'
            process_task.message = f'{issue_key} 处理完成'
            process_task.finished_at = timezone.now()
            process_task.save(update_fields=['status', 'progress', 'stage', 'message', 'finished_at', 'updated_at'])
            IssueProcessResult.objects.update_or_create(
                process_task=process_task,
                defaults={
                    'issue_key': issue_key,
                    'summary': summary,
                    'result_status': 'SUCCESS',
                    'reply_text': reply_text,
                    'can_trace_image': can_img_path or '',
                    'can_trace_image_url': self._to_media_url(can_img_path),
                    'error_message': '',
                },
            )
            publish_rule_group_snapshot()

    return _IssueProcessPipeline(*args, process_task_id=process_task_id, **kwargs)
