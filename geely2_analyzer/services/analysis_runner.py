import json
import logging
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from geely2_analyzer.models import Geely2AnalysisResult, Geely2AnalysisTask
from geely2_analyzer.services.analysis_prompts import (
    EXTRACT_RELATED_SIGNALS_PROMPT,
    EXTRACT_UPPER_REQUIREMENTS_PROMPT,
    FINAL_ANALYSIS_PROMPT,
)
from geely2_analyzer.services.client_factory import build_ai_client, build_jira_client
from geely2_analyzer.services.pipeline_helpers import (
    collect_bosch_signal_logs,
    recursive_unpack_archives,
    select_latest_cycles,
)
from geely2_analyzer.services.stream import publish_geely2_snapshot
from legacy_core.ai_client_by_langchain import safe_parse_json
from legacy_core.jira_utils import get_jira_comments

logger = logging.getLogger('geely2_analyzer')


def _update_task(task, **kwargs):
    update_fields = ['updated_at']
    for field, value in kwargs.items():
        setattr(task, field, value)
        update_fields.append(field)
    if 'status' in kwargs and kwargs['status'] in ('SUCCESS', 'FAILED'):
        task.finished_at = timezone.now()
        update_fields.append('finished_at')
    task.save(update_fields=update_fields)
    publish_geely2_snapshot(task.user)


def download_qnx_attachment(issue, workspace_dir: Path):
    workspace_dir.mkdir(parents=True, exist_ok=True)
    for attachment in getattr(issue.fields, 'attachment', []) or []:
        if getattr(attachment, 'filename', '') != 'qnx_log.tgz':
            continue
        target_path = workspace_dir / 'qnx_log.tgz'
        target_path.write_bytes(attachment.get())
        return str(target_path)
    raise FileNotFoundError('qnx_log.tgz not found')


def run_analysis_task(task_id):
    task = Geely2AnalysisTask.objects.select_related(
        'user', 'credential_binding', 'issue_snapshot',
    ).get(pk=task_id)

    try:
        jira_client = build_jira_client(task.credential_binding)
        ai_client = build_ai_client()

        workspace_dir = Path(getattr(settings, 'MEDIA_ROOT', '/tmp')) / 'geely2' / task.issue_key / str(task.id)
        task.workspace_dir = str(workspace_dir)
        task.save(update_fields=['workspace_dir', 'updated_at'])

        issue = jira_client.get_issue(task.issue_key)
        _update_task(task, stage='FETCH_COMMENTS', progress=10, message='正在拉取 Jira 评论')
        comments_text = get_jira_comments(issue)

        _update_task(task, stage='EXTRACT_RELATED_SIGNALS', progress=20, message='正在提取相关信号')
        extracted_signals = ai_client.chat_by_langchain(
            '', EXTRACT_RELATED_SIGNALS_PROMPT.format(comments=comments_text),
        )
        signal_list = (
            [] if extracted_signals == '无法提取'
            else [item.strip() for item in extracted_signals.split(',') if item.strip()]
        )

        _update_task(task, stage='DOWNLOAD_ARCHIVES', progress=35, message='正在下载 qnx_log.tgz')
        download_dir = workspace_dir / 'downloads'
        download_qnx_attachment(issue, download_dir)

        _update_task(task, stage='UNPACK_QNX_LOG', progress=50, message='正在递归解压 qnx 日志')
        recursive_unpack_archives(download_dir)

        _update_task(task, stage='SELECT_TARGET_CYCLES', progress=60, message='正在选择最新 cycle')
        cycle_paths = select_latest_cycles(list(download_dir.rglob('cycle_*')))
        if not cycle_paths:
            _update_task(
                task,
                status='FAILED',
                stage='SELECT_TARGET_CYCLES',
                progress=60,
                message='未发现有效 cycle',
                error_code='CYCLE_NOT_FOUND',
                error_message='未发现有效 cycle',
            )
            return

        _update_task(task, stage='FILTER_BOSCH_LOGS', progress=75, message='正在提取 Bosch 日志')
        grouped_logs = collect_bosch_signal_logs(cycle_paths, signal_list)

        _update_task(task, stage='EXTRACT_UPPER_REQUIREMENTS', progress=85, message='正在提取上层需求')
        requirements_summary = ai_client.chat_by_langchain(
            '', EXTRACT_UPPER_REQUIREMENTS_PROMPT.format(comments=comments_text),
        )

        _update_task(task, stage='AI_ANALYZE', progress=95, message='正在生成最终结论')
        final_raw = ai_client.chat_by_langchain(
            '', FINAL_ANALYSIS_PROMPT.format(
                requirements=requirements_summary,
                grouped_logs=json.dumps(grouped_logs, ensure_ascii=False),
            ),
        )
        final_payload = safe_parse_json(final_raw)

        _update_task(task, status='SUCCESS', stage='SAVE_RESULT', progress=100, message='分析完成')

        Geely2AnalysisResult.objects.update_or_create(
            analysis_task=task,
            defaults={
                'user': task.user,
                'issue_key': task.issue_key,
                'ai_summary': final_payload.get('analysis_summary', ''),
                'reply_text': final_payload.get('reply_text', ''),
                'evidence_payload': {
                    'signals': signal_list,
                    'requirements_summary': requirements_summary,
                    'grouped_logs': grouped_logs,
                    'cycle_names': [path.name for path in cycle_paths],
                },
                'confidence': final_payload.get('confidence', 0),
                'risk_notes': final_payload.get('risk_notes', ''),
                'needs_user_confirmation': True,
            },
        )

        task.issue_snapshot.current_analysis_status = 'SUCCESS'
        task.issue_snapshot.save(update_fields=['current_analysis_status', 'updated_at'])

    except Exception as exc:
        _update_task(
            task,
            status='FAILED',
            message='分析失败',
            error_message=str(exc),
        )
        logger.exception('Analysis task %s failed', task_id)
