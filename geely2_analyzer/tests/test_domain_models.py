from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, override_settings

from ..models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    Geely2SyncTask,
    JiraCredentialBinding,
)
from ..serializers import JiraCredentialBindingSerializer
from ..services.credential_crypto import decrypt_secret, encrypt_secret


TEST_ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class Geely2DomainModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_model_user',
            password='Geely2Pass123!',
        )
        self.other_user = get_user_model().objects.create_user(
            username='geely_other_user',
            password='Geely2Pass123!',
        )

    def _create_binding(self, user, project_code='geely2'):
        return JiraCredentialBinding.objects.create(
            user=user,
            project_code=project_code,
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username=f'{user.username}@example.com',
            encrypted_password=encrypt_secret('jira-password'),
        )

    def test_encrypt_and_decrypt_secret_round_trip(self):
        encrypted = encrypt_secret('jira-password')
        self.assertNotEqual(encrypted, 'jira-password')
        self.assertEqual(decrypt_secret(encrypted), 'jira-password')

    @override_settings(DEBUG=True, JIRA_CREDENTIAL_ENCRYPTION_KEY='')
    def test_encrypt_secret_requires_explicit_key(self):
        with self.assertRaises(ImproperlyConfigured):
            encrypt_secret('jira-password')

    def test_credential_binding_serializer_hides_encrypted_password(self):
        binding = self._create_binding(self.user)

        serialized = JiraCredentialBindingSerializer(binding).data

        self.assertNotIn('encrypted_password', serialized)

    def test_credential_binding_encrypts_plaintext_password_on_save(self):
        binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='plain@example.com',
            encrypted_password='plain-secret',
        )

        self.assertNotEqual(binding.encrypted_password, 'plain-secret')
        self.assertEqual(decrypt_secret(binding.encrypted_password), 'plain-secret')

    def test_issue_snapshot_is_unique_per_user_and_issue_key(self):
        Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-1', summary='A')
        with self.assertRaises(IntegrityError):
            Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-1', summary='B')

    def test_sync_task_requires_binding_owned_by_same_user(self):
        other_binding = self._create_binding(self.other_user)

        with self.assertRaises(ValidationError):
            Geely2SyncTask.objects.create(user=self.user, credential_binding=other_binding)

    def test_issue_snapshot_requires_sync_task_owned_by_same_user(self):
        other_binding = self._create_binding(self.other_user)
        other_sync_task = Geely2SyncTask.objects.create(
            user=self.other_user,
            credential_binding=other_binding,
        )

        with self.assertRaises(ValidationError):
            Geely2IssueSnapshot.objects.create(
                user=self.user,
                last_sync_task=other_sync_task,
                issue_key='GEELY2-3',
            )

    def test_analysis_task_requires_related_objects_owned_by_same_user(self):
        user_binding = self._create_binding(self.user)
        other_binding = self._create_binding(self.other_user)
        user_snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-4')

        with self.assertRaises(ValidationError):
            Geely2AnalysisTask.objects.create(
                user=self.user,
                credential_binding=other_binding,
                issue_snapshot=user_snapshot,
                issue_key='GEELY2-4',
            )

        other_sync_task = Geely2SyncTask.objects.create(
            user=self.other_user,
            credential_binding=other_binding,
        )
        other_snapshot = Geely2IssueSnapshot.objects.create(
            user=self.other_user,
            last_sync_task=other_sync_task,
            issue_key='GEELY2-5',
        )

        with self.assertRaises(ValidationError):
            Geely2AnalysisTask.objects.create(
                user=self.user,
                credential_binding=user_binding,
                issue_snapshot=other_snapshot,
                issue_key='GEELY2-5',
            )

    def test_analysis_task_requires_matching_snapshot_issue_key(self):
        binding = self._create_binding(self.user)
        snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-7')

        with self.assertRaises(ValidationError):
            Geely2AnalysisTask.objects.create(
                user=self.user,
                credential_binding=binding,
                issue_snapshot=snapshot,
                issue_key='GEELY2-7-MISMATCH',
            )

    def test_analysis_task_requires_non_blank_issue_key(self):
        binding = self._create_binding(self.user)
        snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-7-REQUIRED')

        with self.assertRaises(ValidationError):
            Geely2AnalysisTask.objects.create(
                user=self.user,
                credential_binding=binding,
                issue_snapshot=snapshot,
                issue_key='',
            )

    def test_analysis_task_bulk_create_validates_constraints(self):
        other_binding = self._create_binding(self.other_user)
        snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-7-BULK')

        with self.assertRaises(ValidationError):
            Geely2AnalysisTask.objects.bulk_create([
                Geely2AnalysisTask(
                    user=self.user,
                    credential_binding=other_binding,
                    issue_snapshot=snapshot,
                    issue_key='GEELY2-7-BULK',
                )
            ])

    def test_analysis_result_is_one_to_one_with_analysis_task(self):
        binding = self._create_binding(self.user)
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

    def test_analysis_result_requires_task_owned_by_same_user(self):
        other_binding = self._create_binding(self.other_user)
        other_sync_task = Geely2SyncTask.objects.create(
            user=self.other_user,
            credential_binding=other_binding,
        )
        other_snapshot = Geely2IssueSnapshot.objects.create(
            user=self.other_user,
            last_sync_task=other_sync_task,
            issue_key='GEELY2-6',
        )
        other_task = Geely2AnalysisTask.objects.create(
            user=self.other_user,
            credential_binding=other_binding,
            issue_snapshot=other_snapshot,
            issue_key='GEELY2-6',
        )

        with self.assertRaises(ValidationError):
            Geely2AnalysisResult.objects.create(
                analysis_task=other_task,
                user=self.user,
                issue_key='GEELY2-6',
                reply_text='跨用户结果',
            )

    def test_analysis_result_requires_matching_task_issue_key(self):
        binding = self._create_binding(self.user)
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=binding)
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-8',
        )
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-8',
        )

        with self.assertRaises(ValidationError):
            Geely2AnalysisResult.objects.create(
                analysis_task=task,
                user=self.user,
                issue_key='GEELY2-8-MISMATCH',
                reply_text='错误 issue 结果',
            )

    def test_analysis_result_requires_non_blank_issue_key(self):
        binding = self._create_binding(self.user)
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=binding)
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-8-REQUIRED',
        )
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-8-REQUIRED',
        )

        with self.assertRaises(ValidationError):
            Geely2AnalysisResult.objects.create(
                analysis_task=task,
                user=self.user,
                issue_key='',
                reply_text='空 issue 结果',
            )

    def test_analysis_result_bulk_create_validates_constraints(self):
        binding = self._create_binding(self.user)
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=binding)
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-8-BULK',
        )
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-8-BULK',
        )

        with self.assertRaises(ValidationError):
            Geely2AnalysisResult.objects.bulk_create([
                Geely2AnalysisResult(
                    analysis_task=task,
                    user=self.user,
                    issue_key='GEELY2-8-BULK-MISMATCH',
                    reply_text='批量错误 issue 结果',
                )
            ])

    def test_queryset_update_is_blocked_for_validated_models(self):
        binding = self._create_binding(self.user)
        snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-UPDATE')
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-UPDATE',
        )

        with self.assertRaises(RuntimeError):
            Geely2AnalysisTask.objects.filter(pk=task.pk).update(issue_key='GEELY2-MISMATCH')