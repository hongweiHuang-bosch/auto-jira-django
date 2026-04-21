from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from geely2_analyzer.models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    JiraCredentialBinding,
)


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode('utf-8'))
class Geely2AnalysisWorkerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_worker_result',
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
            issue_key='GEELY2-121',
            summary='音频爆音',
        )
        self.task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            issue_snapshot=self.snapshot,
            issue_key='GEELY2-121',
        )

    @patch('geely2_analyzer.services.analysis_runner.select_latest_cycles')
    @patch('geely2_analyzer.services.analysis_runner.recursive_unpack_archives')
    @patch('geely2_analyzer.services.analysis_runner.download_qnx_attachment')
    @patch('geely2_analyzer.services.analysis_runner.collect_bosch_signal_logs')
    @patch('geely2_analyzer.services.analysis_runner.build_ai_client')
    @patch('geely2_analyzer.services.analysis_runner.build_jira_client')
    def test_run_geely2_worker_persists_analysis_result(
        self, mock_build_jira, mock_build_ai, mock_collect_logs,
        mock_download, mock_unpack, mock_select_cycles,
    ):
        fake_issue = type('Issue', (), {
            'key': 'GEELY2-121',
            'fields': type('Fields', (), {
                'summary': '音频爆音',
                'status': type('Status', (), {'name': 'Open'})(),
                'comment': type('CommentHolder', (), {'comments': []})(),
                'attachment': [],
            })(),
        })()
        mock_build_jira.return_value.get_issue.return_value = fake_issue
        mock_download.return_value = '/tmp/qnx_log.tgz'
        mock_unpack.return_value = []
        from pathlib import Path
        mock_select_cycles.return_value = [Path('/tmp/cycle_12')]
        mock_collect_logs.return_value = {
            'cycle_12': [
                {'timestamp': '2026-04-21 10:00:01.000', 'line': '2026-04-21 10:00:01.000 BoschVehicleHal SIG_A 1'},
            ],
        }
        mock_build_ai.return_value.chat_by_langchain.side_effect = [
            'SIG_A',
            '上层希望确认 SIG_A 从 1 变成 0 的原因',
            '{"analysis_summary": "日志显示 SIG_A 在 Bosch 侧发生变化", "reply_text": "请继续确认 Bosch 日志中 SIG_A 的变化原因", "confidence": 0.8, "risk_notes": "无"}',
        ]

        call_command('run_geely2_worker', '--once')

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'SUCCESS')
        self.assertTrue(Geely2AnalysisResult.objects.filter(analysis_task=self.task).exists())
