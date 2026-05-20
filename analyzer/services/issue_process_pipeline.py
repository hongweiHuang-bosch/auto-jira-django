from __future__ import annotations

from pathlib import Path
import logging

from django.conf import settings
from django.utils import timezone

from analyzer.models import IssueProcessResult, IssueProcessTask
from analyzer.services.cantrace_payload import build_raw_signals_json
from analyzer.services.rule_group_stream import publish_rule_group_snapshot

logger = logging.getLogger('jira_analyzer_worker')

def create_issue_process_pipeline(*args, process_task_id: int, **kwargs):
    """Lazy factory to avoid importing Pipeline (and its ML deps) at module load time."""
    from legacy_core.pipeline import Pipeline

    class _IssueProcessPipeline(Pipeline):
        def __init__(self, *a, process_task_id: int, **kw):
            super().__init__(*a, **kw)
            self.process_task_id = process_task_id

        def _update_progress(self, stage: str, progress: int, message: str = ''):
            """覆写 Pipeline 的空钩子，实时写入处理进度。"""
            IssueProcessTask.objects.filter(pk=self.process_task_id).update(
                stage=stage,
                progress=progress,
                message=message,
                updated_at=timezone.now(),
            )
            publish_rule_group_snapshot()

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

        def _finalize_issue(
            self,
            issue_key: str,
            summary: str,
            reply_text: str,
            can_img_path: str,
            can_trace_outputs: str = '',
            upper_comment: str = '',
        ):
            process_task = IssueProcessTask.objects.get(pk=self.process_task_id)
            process_task.status = 'SUCCESS'
            process_task.progress = 100
            process_task.stage = 'SAVING_RESULT'
            process_task.message = f'{issue_key} 处理完成'
            process_task.error_message = ''
            process_task.finished_at = timezone.now()
            process_task.save(update_fields=['status', 'progress', 'stage', 'message', 'error_message', 'finished_at', 'updated_at'])
            raw_signals = build_raw_signals_json(can_trace_outputs)
            logger.info(
                'saving process result issue=%s raw_signals_present=%s upper_comment_len=%s',
                issue_key,
                bool(raw_signals),
                len(upper_comment or ''),
            )
            IssueProcessResult.objects.update_or_create(
                process_task=process_task,
                defaults={
                    'issue_key': issue_key,
                    'summary': summary,
                    'result_status': 'SUCCESS',
                    'reply_text': reply_text,
                    'upper_comment': upper_comment,
                    'can_trace_image': can_img_path or '',
                    'can_trace_image_url': self._to_media_url(can_img_path),
                    'raw_signals': raw_signals,
                    'error_message': '',
                },
            )
            publish_rule_group_snapshot()

    return _IssueProcessPipeline(*args, process_task_id=process_task_id, **kwargs)
