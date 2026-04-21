from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from geely2_analyzer.models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    Geely2SyncTask,
    JiraCredentialBinding,
)
from geely2_analyzer.services.credential_crypto import decrypt_secret, encrypt_secret


class Geely2DomainModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_model_user',
            password='Geely2Pass123!',
        )

    def test_encrypt_and_decrypt_secret_round_trip(self):
        encrypted = encrypt_secret('jira-password')
        self.assertNotEqual(encrypted, 'jira-password')
        self.assertEqual(decrypt_secret(encrypted), 'jira-password')

    def test_issue_snapshot_is_unique_per_user_and_issue_key(self):
        Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-1', summary='A')
        with self.assertRaises(IntegrityError):
            Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-1', summary='B')

    def test_analysis_result_is_one_to_one_with_analysis_task(self):
        binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='user@example.com',
            encrypted_password=encrypt_secret('jira-password'),
        )
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=binding)
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-2',
            summary='方向盘异响',
        )
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-2',
        )
        Geely2AnalysisResult.objects.create(
            analysis_task=task,
            user=self.user,
            issue_key='GEELY2-2',
            reply_text='建议检查 Bosch 日志',
        )
        with self.assertRaises(IntegrityError):
            Geely2AnalysisResult.objects.create(
                analysis_task=task,
                user=self.user,
                issue_key='GEELY2-2',
                reply_text='重复结果',
            )