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
            encrypted_password='jira-password',
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

    def test_credential_binding_preserves_existing_ciphertext_on_save(self):
        original_key = Fernet.generate_key().decode('utf-8')
        rotated_key = Fernet.generate_key().decode('utf-8')

        with override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=original_key):
            binding = JiraCredentialBinding.objects.create(
                user=self.user,
                project_code='geely2',
                jira_base_url='https://boolbool.atlassian.net/',
                jira_username='cipher@example.com',
                encrypted_password='stable-secret',
            )

        original_ciphertext = binding.encrypted_password

        with override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=rotated_key):
            binding.is_active = False
            binding.save()

        self.assertEqual(binding.encrypted_password, original_ciphertext)

    def test_credential_binding_bulk_create_encrypts_plaintext_password(self):
        JiraCredentialBinding.objects.bulk_create([
            JiraCredentialBinding(
                user=self.user,
                project_code='geely2',
                jira_base_url='https://boolbool.atlassian.net/',
                jira_username='bulk@example.com',
                encrypted_password='bulk-secret',
            )
        ])

        binding = JiraCredentialBinding.objects.get(user=self.user, project_code='geely2')

        self.assertNotEqual(binding.encrypted_password, 'bulk-secret')
        self.assertEqual(decrypt_secret(binding.encrypted_password), 'bulk-secret')

    def test_credential_binding_encrypts_plaintext_password_with_prefix_like_value(self):
        binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='prefix@example.com',
            encrypted_password='enc::plain-secret',
        )

        self.assertNotEqual(binding.encrypted_password, 'enc::plain-secret')
        self.assertEqual(decrypt_secret(binding.encrypted_password), 'enc::plain-secret')

    def test_credential_binding_encrypts_foreign_token_wrapped_with_prefix_as_plaintext(self):
        foreign_key = Fernet.generate_key().decode('utf-8')
        foreign_token = Fernet(foreign_key.encode('utf-8')).encrypt(b'foreign-secret').decode('utf-8')
        plaintext = f'enc::{foreign_token}'

        binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='foreign-token@example.com',
            encrypted_password=plaintext,
        )

        self.assertNotEqual(binding.encrypted_password, plaintext)
        self.assertEqual(decrypt_secret(binding.encrypted_password), plaintext)

    def test_credential_binding_queryset_update_is_blocked(self):
        binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='update@example.com',
            encrypted_password='update-secret',
        )

        with self.assertRaises(RuntimeError):
            JiraCredentialBinding.objects.filter(pk=binding.pk).update(encrypted_password='plain-update')

    def test_credential_binding_base_manager_update_is_blocked(self):
        binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='base-update@example.com',
            encrypted_password='base-update-secret',
        )

        with self.assertRaises(RuntimeError):
            JiraCredentialBinding._base_manager.filter(pk=binding.pk).update(encrypted_password='plain-bypass')

    def test_credential_binding_base_manager_bulk_create_encrypts_plaintext_password(self):
        JiraCredentialBinding._base_manager.bulk_create([
            JiraCredentialBinding(
                user=self.user,
                project_code='geely2',
                jira_base_url='https://boolbool.atlassian.net/',
                jira_username='base-bulk@example.com',
                encrypted_password='base-bulk-secret',
            )
        ])

        binding = JiraCredentialBinding.objects.get(user=self.user, project_code='geely2')

        self.assertNotEqual(binding.encrypted_password, 'base-bulk-secret')
        self.assertEqual(decrypt_secret(binding.encrypted_password), 'base-bulk-secret')

    def test_credential_binding_user_cannot_change_after_creation(self):
        binding = self._create_binding(self.user)

        binding.user = self.other_user

        with self.assertRaises(ValidationError):
            binding.save()

    def test_sync_task_requires_credential_binding_when_saving(self):
        with self.assertRaises(ValidationError):
            Geely2SyncTask(user=self.user).save()

    def test_sync_task_credential_binding_cannot_change_after_creation(self):
        primary_binding = self._create_binding(self.user)
        alternate_binding = self._create_binding(self.user, project_code='geely2_alt')
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=primary_binding)

        sync_task.credential_binding = alternate_binding

        with self.assertRaises(ValidationError):
            sync_task.save()

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

    def test_issue_snapshot_issue_key_cannot_change_after_analysis_task_exists(self):
        binding = self._create_binding(self.user)
        snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-CHAIN')
        Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-CHAIN',
        )

        snapshot.issue_key = 'GEELY2-CHAIN-CHANGED'

        with self.assertRaises(ValidationError):
            snapshot.save()

    def test_issue_snapshot_last_sync_task_can_refresh_after_analysis_task_exists(self):
        binding = self._create_binding(self.user)
        first_sync_task = Geely2SyncTask.objects.create(
            user=self.user,
            credential_binding=binding,
            status='SUCCESS',
        )
        second_sync_task = Geely2SyncTask.objects.create(
            user=self.user,
            credential_binding=binding,
            status='SUCCESS',
        )
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=first_sync_task,
            issue_key='GEELY2-SNAPSHOT-LOCK',
        )
        Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-SNAPSHOT-LOCK',
        )

        snapshot.last_sync_task = second_sync_task

        snapshot.save()

        self.assertEqual(snapshot.last_sync_task_id, second_sync_task.id)

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

    def test_analysis_task_base_manager_bulk_create_validates_constraints(self):
        other_binding = self._create_binding(self.other_user)
        snapshot = Geely2IssueSnapshot.objects.create(user=self.user, issue_key='GEELY2-7-BASE-BULK')

        with self.assertRaises(ValidationError):
            Geely2AnalysisTask._base_manager.bulk_create([
                Geely2AnalysisTask(
                    user=self.user,
                    credential_binding=other_binding,
                    issue_snapshot=snapshot,
                    issue_key='GEELY2-7-BASE-BULK',
                )
            ])

    def test_analysis_task_requires_relations_when_saving(self):
        with self.assertRaises(ValidationError):
            Geely2AnalysisTask(user=self.user, issue_key='GEELY2-MISSING-RELATIONS').save()

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

    def test_analysis_task_credential_binding_cannot_change_after_creation(self):
        primary_binding = self._create_binding(self.user)
        alternate_binding = self._create_binding(self.user, project_code='geely2_binding_alt')
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=primary_binding)
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-TASK-LOCK',
        )
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=primary_binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-TASK-LOCK',
        )

        task.credential_binding = alternate_binding

        with self.assertRaises(ValidationError):
            task.save()

    def test_analysis_task_issue_snapshot_cannot_change_after_creation(self):
        binding = self._create_binding(self.user)
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=binding)
        original_snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-TASK-SNAPSHOT-LOCK',
        )
        replacement_snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-TASK-SNAPSHOT-ALT',
        )
        task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=binding,
            issue_snapshot=original_snapshot,
            issue_key='GEELY2-TASK-SNAPSHOT-LOCK',
        )

        task.issue_snapshot = replacement_snapshot
        task.issue_key = 'GEELY2-TASK-SNAPSHOT-ALT'

        with self.assertRaises(ValidationError):
            task.save()

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

    def test_analysis_result_analysis_task_cannot_change_after_save(self):
        primary_binding = self._create_binding(self.user)
        alternate_binding = self._create_binding(self.user, project_code='geely2_result_alt')
        sync_task = Geely2SyncTask.objects.create(user=self.user, credential_binding=primary_binding)
        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-RESULT-LOCK',
        )
        first_task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=primary_binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-RESULT-LOCK',
        )
        second_task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=alternate_binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-RESULT-LOCK',
        )
        result = Geely2AnalysisResult.objects.create(
            analysis_task=first_task,
            user=self.user,
            issue_key='GEELY2-RESULT-LOCK',
            reply_text='固定结果',
        )

        result.analysis_task = second_task

        with self.assertRaises(ValidationError):
            result.save()

    def test_analysis_result_requires_analysis_task_when_saving(self):
        with self.assertRaises(ValidationError):
            Geely2AnalysisResult(user=self.user, issue_key='GEELY2-MISSING-TASK').save()

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