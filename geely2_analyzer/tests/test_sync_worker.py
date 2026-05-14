from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from geely2_analyzer.models import (
    Geely2IssueSnapshot,
    Geely2SyncTask,
    JiraCredentialBinding,
)


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode('utf-8'))
class Geely2SyncWorkerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_worker_user',
            password='Geely2Pass123!',
        )
        self.binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='user@example.com',
            encrypted_password='jira-password',
            is_active=True,
        )
        self.task = Geely2SyncTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            status='PENDING',
            message='同步任务已创建',
        )

    @patch('geely2_analyzer.services.sync_runner.build_jira_client')
    def test_run_geely2_worker_persists_snapshots(self, mock_build_jira_client):
        fake_issue = type('Issue', (), {
            'key': 'GEELY2-88',
            'fields': type('Fields', (), {
                'summary': '仪表黑屏',
                'assignee': type('Assignee', (), {'displayName': 'Xin SHEN'})(),
                'updated': '2026-04-21T10:30:00.000+0800',
            })(),
        })()
        mock_build_jira_client.return_value.search_issues.return_value = [fake_issue]

        call_command('run_geely2_worker', '--once')

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'SUCCESS')
        self.assertTrue(
            Geely2IssueSnapshot.objects.filter(user=self.user, issue_key='GEELY2-88').exists()
        )

    @patch('geely2_analyzer.services.sync_runner.build_jira_client')
    def test_worker_removes_stale_snapshots(self, mock_build_jira_client):
        """已有快照但 Jira 不再返回该票，应该被清除。"""
        Geely2IssueSnapshot.objects.create(
            user=self.user,
            issue_key='GEELY2-OLD',
            summary='旧问题',
        )

        fake_issue = type('Issue', (), {
            'key': 'GEELY2-NEW',
            'fields': type('Fields', (), {
                'summary': '新问题',
                'assignee': type('Assignee', (), {'displayName': 'Test'})(),
                'updated': '2026-04-21T11:00:00.000+0800',
            })(),
        })()
        mock_build_jira_client.return_value.search_issues.return_value = [fake_issue]

        call_command('run_geely2_worker', '--once')

        self.assertFalse(
            Geely2IssueSnapshot.objects.filter(user=self.user, issue_key='GEELY2-OLD').exists()
        )
        self.assertTrue(
            Geely2IssueSnapshot.objects.filter(user=self.user, issue_key='GEELY2-NEW').exists()
        )

    @patch('geely2_analyzer.services.sync_runner.build_jira_client')
    def test_worker_marks_task_failed_on_jira_error(self, mock_build_jira_client):
        mock_build_jira_client.return_value.search_issues.side_effect = Exception('Jira连接失败')

        call_command('run_geely2_worker', '--once')

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'FAILED')
        self.assertIn('Jira连接失败', self.task.error_message)
