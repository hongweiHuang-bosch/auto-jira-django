from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from analyzer.models import IssueLearningMemory
from geely2_analyzer.models import Geely2AnalysisTask, Geely2IssueSnapshot, JiraCredentialBinding
from geely2_analyzer.services.analysis_runner import run_analysis_task


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode('utf-8'))
class Geely2LearningMemoryIntegrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_learning_user',
            password='Geely2Pass123!',
        )
        self.binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='user@example.com',
            encrypted_password='jira-password',
        )
        self.snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            issue_key='GEELY2-220',
            summary='音频爆音',
        )
        self.task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            issue_snapshot=self.snapshot,
            issue_key='GEELY2-220',
        )

    def _build_issue(self):
        return type('Issue', (), {
            'key': 'GEELY2-220',
            'fields': type('Fields', (), {
                'summary': '音频爆音',
                'status': type('Status', (), {'name': 'Open'})(),
                'comment': type('CommentHolder', (), {'comments': []})(),
                'attachment': [],
            })(),
        })()

    def _create_memory(self, root, *, issue_key, content):
        role_dir = Path(root) / 'role_0'
        role_dir.mkdir(parents=True, exist_ok=True)
        file_path = role_dir / f'{issue_key}.json'
        file_path.write_text(content, encoding='utf-8')
        IssueLearningMemory.objects.create(
            role_index=0,
            issue_key=issue_key,
            review_status='FAIL',
            incorrect_conclusion='历史错误结论',
            correct_conclusion='历史正确结论',
            error_reason='历史错误原因',
            signal_summary='SIG_A',
            memory_file_path=str(file_path),
            memory_content_hash=f'hash-{issue_key}',
        )

    @patch('geely2_analyzer.services.analysis_runner.select_latest_cycles')
    @patch('geely2_analyzer.services.analysis_runner.recursive_unpack_archives')
    @patch('geely2_analyzer.services.analysis_runner.download_qnx_attachment')
    @patch('geely2_analyzer.services.analysis_runner.collect_bosch_signal_logs')
    @patch('geely2_analyzer.services.analysis_runner.build_ai_client')
    @patch('geely2_analyzer.services.analysis_runner.build_jira_client')
    def test_run_analysis_task_injects_learning_memories_into_final_prompt(
        self, mock_build_jira, mock_build_ai, mock_collect_logs,
        mock_download, mock_unpack, mock_select_cycles,
    ):
        fake_issue = self._build_issue()
        mock_build_jira.return_value.get_issue.return_value = fake_issue
        mock_download.return_value = '/tmp/qnx_log.tgz'
        mock_unpack.return_value = []
        mock_select_cycles.return_value = [Path('/tmp/cycle_12')]
        mock_collect_logs.return_value = {'cycle_12': [{'line': 'SIG_A changed'}]}
        mock_build_ai.return_value.chat_by_langchain.side_effect = [
            'SIG_A',
            '请确认 SIG_A 的变化原因',
            '{"analysis_summary": "ok", "reply_text": "最终结论", "confidence": 0.7, "risk_notes": "none"}',
        ]

        with TemporaryDirectory() as temp_dir:
            self._create_memory(
                temp_dir,
                issue_key='CASE-1',
                content='{"role_index":0,"issue_key":"CASE-1","requirements":"","comment":"","signal_summary":"SIG_A","qnx_android_logs":"","cantrace_output":"","incorrect_conclusion":"旧错误","error_reason":"忽略 SIG_A","correct_result":"确认 SIG_A 链路","review_status":"FAIL","created_at":"2026-05-18T00:00:00+08:00","updated_at":"2026-05-18T00:00:00+08:00"}',
            )
            with override_settings(LEARNING_MEMORY_ROOT=temp_dir):
                run_analysis_task(self.task.id)

        final_prompt = mock_build_ai.return_value.chat_by_langchain.call_args_list[2].args[1]
        self.assertIn('历史纠错记忆', final_prompt)
        self.assertIn('旧错误', final_prompt)
        self.assertIn('确认 SIG_A 链路', final_prompt)

    @patch('geely2_analyzer.services.analysis_runner.select_latest_cycles')
    @patch('geely2_analyzer.services.analysis_runner.recursive_unpack_archives')
    @patch('geely2_analyzer.services.analysis_runner.download_qnx_attachment')
    @patch('geely2_analyzer.services.analysis_runner.collect_bosch_signal_logs')
    @patch('geely2_analyzer.services.analysis_runner.build_ai_client')
    @patch('geely2_analyzer.services.analysis_runner.build_jira_client')
    def test_run_analysis_task_without_learning_memories_keeps_pipeline_working(
        self, mock_build_jira, mock_build_ai, mock_collect_logs,
        mock_download, mock_unpack, mock_select_cycles,
    ):
        fake_issue = self._build_issue()
        mock_build_jira.return_value.get_issue.return_value = fake_issue
        mock_download.return_value = '/tmp/qnx_log.tgz'
        mock_unpack.return_value = []
        mock_select_cycles.return_value = [Path('/tmp/cycle_12')]
        mock_collect_logs.return_value = {'cycle_12': [{'line': 'SIG_A changed'}]}
        mock_build_ai.return_value.chat_by_langchain.side_effect = [
            'SIG_A',
            '请确认 SIG_A 的变化原因',
            '{"analysis_summary": "ok", "reply_text": "最终结论", "confidence": 0.7, "risk_notes": "none"}',
        ]

        with TemporaryDirectory() as temp_dir:
            with override_settings(LEARNING_MEMORY_ROOT=temp_dir):
                run_analysis_task(self.task.id)

        final_prompt = mock_build_ai.return_value.chat_by_langchain.call_args_list[2].args[1]
        self.assertIn('历史纠错记忆', final_prompt)
        self.assertIn('暂无可复用的历史纠错记忆', final_prompt)
