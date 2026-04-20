from __future__ import annotations

from django.utils import timezone

from analyzer.models import IssueProcessTask
from analyzer.services.issue_process_pipeline import create_issue_process_pipeline
from analyzer.services.rule_group_stream import publish_rule_group_snapshot
from analyzer.services.task_catalog import get_role_entry
from legacy_core.jira_utils import JiraClient
from legacy_core.utils import load_config


def run_issue_process_task(task_id: int):
    process_task = IssueProcessTask.objects.get(pk=task_id)
    try:
        cfg = load_config('config.yaml')
        role_entry = get_role_entry(process_task.filter_task.role_index)
        process_task.status = 'RUNNING'
        process_task.stage = 'PREPARING'
        process_task.started_at = timezone.now()
        process_task.message = '正在准备单票分析'
        process_task.save(update_fields=['status', 'stage', 'started_at', 'message', 'updated_at'])
        publish_rule_group_snapshot()

        from legacy_core.ai_client_by_langchain import AIClient

        jira = JiraClient(
            server=cfg['jira']['server'],
            username=cfg['jira']['username'],
            password=cfg['jira']['password'],
        )
        ai = AIClient(
            base_url=cfg['ai']['base_url'],
            api_key=cfg['ai']['api_key'],
            model=cfg['ai'].get('model', 'Qwen3-32B-FP16'),
            pic_model=cfg['ai'].get('pic_model', 'Qwen3-VL-8B'),
        )
        issues = jira.search_issues(f'issue = {process_task.issue_key}', expand=role_entry.get('expand', 'changelog'))
        if not issues:
            raise ValueError(f'未找到 Jira 票：{process_task.issue_key}')

        pipe = create_issue_process_pipeline(
            jira=jira,
            ai=ai,
            custom_field_name=cfg['jira'].get('field_name', ''),
            paths_cfg={},
            process_task_id=task_id,
        )
        pipe.process_issue_with_model_map(
            issues[0],
            base_paths=role_entry['base_paths'],
            model_to_files=role_entry['model_to_files'],
            fallback_files=role_entry.get('fallback_files'),
            extract_prompt=(role_entry.get('prompts') or {}).get('EXTRACT_SIGNALS_SYSTEM'),
            summary_prompt=(role_entry.get('prompts') or {}).get('LOG_SUMMARY_SYSTEM'),
            compare_prompt=(role_entry.get('prompts') or {}).get('COMPARE_CANTRACE'),
            android_qnx_summary_prompt=(role_entry.get('prompts') or {}).get('ANDROID_QNX_LOG_SUMMARY_SYSTEM'),
            requirement_extract_prompt=(role_entry.get('prompts') or {}).get('REQUIREMENT_EXTRACT_SYSTEM'),
            consistency_prompt=(role_entry.get('prompts') or {}).get('CONSISTENCY_SYSTEM'),
        )
    except Exception as e:
        process_task.refresh_from_db()
        if process_task.status != 'FAILED':
            process_task.status = 'FAILED'
            process_task.error_message = str(e)
            process_task.finished_at = timezone.now()
            process_task.save(update_fields=['status', 'error_message', 'finished_at', 'updated_at'])
        publish_rule_group_snapshot()
