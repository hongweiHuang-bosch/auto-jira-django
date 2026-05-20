
from __future__ import annotations
import logging
from pathlib import Path
from django.conf import settings
from analyzer.models import AnalysisTask, IssueAnalysisResult
from analyzer.services.cantrace_payload import build_raw_signals_json
from .task_stream import publish_groups_snapshot
from legacy_core.pipeline import Pipeline

logger = logging.getLogger('jira_analyzer_worker')

class WebPipeline(Pipeline):
    def __init__(self, *args, task_id: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_id = task_id

    def save_true_or_false(self, issue_key):
        return None

    def _error_proces(self, issue_key: str, summary: str, reply_text: str):
        IssueAnalysisResult.objects.update_or_create(
            task_id=self.task_id,
            issue_key=issue_key,
            defaults={
                'summary': summary,
                'result_status': 'MANUAL',
                'reply_text': reply_text,
                'error_message': reply_text,
            }
        )
        publish_groups_snapshot()

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

    def _detect_model_from_issue_dir(self, issue_key: str) -> str:
        comment_dir = Path.cwd() / 'comment'
        if not comment_dir.exists():
            return ''
        for model_dir in comment_dir.iterdir():
            if not model_dir.is_dir():
                continue
            if (model_dir / issue_key).exists():
                return model_dir.name
        return ''

    def _finalize_issue(
        self,
        issue_key: str,
        summary: str,
        reply_text: str,
        can_img_path: str,
        can_trace_outputs: str = '',
        upper_comment: str = '',
    ):
        task = AnalysisTask.objects.get(pk=self.task_id)
        task.message = f'已完成 {issue_key}'
        task.save(update_fields=['message', 'updated_at'])
        raw_signals = build_raw_signals_json(can_trace_outputs)
        logger.info(
            'saving analysis result issue=%s raw_signals_present=%s upper_comment_len=%s',
            issue_key,
            bool(raw_signals),
            len(upper_comment or ''),
        )
        IssueAnalysisResult.objects.update_or_create(
            task_id=self.task_id,
            issue_key=issue_key,
            defaults={
                'summary': summary,
                'model': self._detect_model_from_issue_dir(issue_key),
                'result_status': 'SUCCESS',
                'reply_text': reply_text,
                'can_trace_image': can_img_path or '',
                'can_trace_image_url': self._to_media_url(can_img_path),
                'raw_signals': raw_signals,
                'error_message': '',
            }
        )
        publish_groups_snapshot()
