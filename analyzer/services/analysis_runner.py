
from __future__ import annotations
import logging
from django.db import close_old_connections
from analyzer.models import AnalysisTask
from legacy_core.utils import load_config, setup_logging
from legacy_core.jira_utils import JiraClient
from legacy_core.ai_client_by_langchain import AIClient
from .task_catalog import get_role_entry, get_role_label
from .task_stream import publish_groups_snapshot
from .web_pipeline import WebPipeline

logger = logging.getLogger('jira_analyzer_web')


class AnalysisRunner:
    def __init__(self, task_id: int):
        self.task_id = task_id

    def run(self):
        '''
        实际任务执行器
        '''
        close_old_connections()
        setup_logging()
        task = AnalysisTask.objects.get(pk=self.task_id)
        try:
            role_entry = get_role_entry(task.role_index)
            role_label = task.role_label or get_role_label(task.role_index, role_entry)
            cfg = load_config('config.yaml')
            jira_cfg = cfg['jira']
            ai_cfg = cfg['ai']

            jira = JiraClient(
                server=jira_cfg['server'],
                username=jira_cfg['username'],
                password=jira_cfg['password'],
            )
            ai = AIClient(
                base_url=ai_cfg['base_url'],
                api_key=ai_cfg['api_key'],
                model=ai_cfg.get('model', 'Qwen3-32B-FP16'),
                pic_model=ai_cfg.get('pic_model', 'Qwen3-VL-8B'),
                connect_timeout=ai_cfg.get('connect_timeout', 10),
                read_timeout=ai_cfg.get('read_timeout', 300),
                max_retries=ai_cfg.get('max_retries', 3),
                use_system_proxy=ai_cfg.get('use_system_proxy', False),
                proxies=ai_cfg.get('proxies'),
            )

            task.status = 'RUNNING'
            task.progress = 0
            task.total_groups = 1
            task.finished_groups = 0
            task.message = f'{role_label} 分析开始'
            task.save(update_fields=['status', 'progress', 'total_groups', 'finished_groups', 'message', 'updated_at'])
            logger.info('analysis runner started', extra={'task_id': self.task_id, 'role_label': role_label})
            publish_groups_snapshot()

            pipe = WebPipeline(
                jira=jira,
                ai=ai,
                custom_field_name=jira_cfg.get('field_name', ''),
                paths_cfg={},
                task_id=self.task_id,
            )
            task.message = f"正在处理 {role_label}: {role_entry['jql'][:120]}"
            task.save(update_fields=['message', 'updated_at'])
            logger.info('analysis runner batch starting', extra={'task_id': self.task_id, 'role_label': role_label})
            publish_groups_snapshot()

            pipe.run_batch_with_model_map(
                jql=role_entry['jql'],
                expand=role_entry.get('expand', 'changelog'),
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
            task.finished_groups = 1
            task.progress = 100
            task.message = f'{role_label} 已完成'
            task.save(update_fields=['finished_groups', 'progress', 'message', 'updated_at'])
            logger.info('analysis runner batch done', extra={'task_id': self.task_id, 'role_label': role_label})
            publish_groups_snapshot()

            task.status = 'SUCCESS'
            task.progress = 100
            task.message = f'{role_label} 分析完成'
            task.save(update_fields=['status', 'progress', 'message', 'updated_at'])
            logger.info('analysis runner succeeded', extra={'task_id': self.task_id, 'role_label': role_label})
            publish_groups_snapshot()
        except Exception as exc:
            logger.exception('分析任务失败: %s', exc)
            task.status = 'FAILED'
            task.message = str(exc)
            task.save(update_fields=['status', 'message', 'updated_at'])
            publish_groups_snapshot()
        finally:
            close_old_connections()
