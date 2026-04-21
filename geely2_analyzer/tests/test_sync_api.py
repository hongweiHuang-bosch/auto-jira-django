from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from geely2_analyzer.models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    Geely2SyncTask,
    JiraCredentialBinding,
)


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode('utf-8'))
class Geely2SyncApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='geely_sync_user',
            password='Geely2Pass123!',
        )
        self.client.force_login(self.user)
        self.binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='user@example.com',
            encrypted_password='jira-password',
            is_active=True,
        )

    def test_sync_endpoints_require_session_authentication(self):
        anonymous_client = Client()

        create_response = anonymous_client.post('/api/geely2/sync-tasks/')
        issues_response = anonymous_client.get('/api/geely2/issues/')
        stream_response = anonymous_client.get('/api/geely2/stream/')

        self.assertEqual(create_response.status_code, 401)
        self.assertEqual(issues_response.status_code, 401)
        self.assertEqual(stream_response.status_code, 401)

    def test_create_sync_task_requires_credential_binding(self):
        self.binding.delete()

        response = self.client.post('/api/geely2/sync-tasks/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], '请先配置 Jira 凭据')

    def test_create_sync_task_rejects_running_task(self):
        task = Geely2SyncTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            status='RUNNING',
            message='同步进行中',
        )

        response = self.client.post('/api/geely2/sync-tasks/')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['task_id'], task.id)

    def test_sync_task_model_rejects_second_active_task_for_same_user(self):
        Geely2SyncTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            status='RUNNING',
            message='同步进行中',
        )

        with self.assertRaisesMessage(ValidationError, 'Another pending or running sync task already exists for this user.'):
            Geely2SyncTask.objects.create(
                user=self.user,
                credential_binding=self.binding,
                status='PENDING',
                message='重复同步任务',
            )

    def test_create_sync_task_and_list_issues(self):
        create_response = self.client.post('/api/geely2/sync-tasks/')

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(Geely2SyncTask.objects.count(), 1)

        sync_task = Geely2SyncTask.objects.first()
        detail_response = self.client.get(f'/api/geely2/sync-tasks/{sync_task.id}/')

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()['id'], sync_task.id)
        self.assertEqual(detail_response.json()['status'], 'PENDING')

        snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-10',
            summary='仪表黑屏',
            assignee='Xin SHEN',
            jira_updated_at=timezone.now(),
            current_analysis_status='IDLE',
        )
        analysis_task = Geely2AnalysisTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            issue_snapshot=snapshot,
            issue_key='GEELY2-10',
        )
        result = Geely2AnalysisResult.objects.create(
            analysis_task=analysis_task,
            user=self.user,
            issue_key='GEELY2-10',
            reply_text='分析完成',
        )

        list_response = self.client.get('/api/geely2/issues/')

        self.assertEqual(list_response.status_code, 200)
        payload = list_response.json()
        self.assertEqual(payload['latest_sync_task']['id'], sync_task.id)
        self.assertEqual(payload['items'][0]['issue_key'], 'GEELY2-10')
        self.assertIsInstance(payload['items'][0]['jira_updated_at'], str)
        self.assertEqual(payload['items'][0]['latest_analysis_task_id'], analysis_task.id)
        self.assertEqual(payload['items'][0]['latest_result_id'], result.id)

    def test_stream_returns_initial_snapshot(self):
        sync_task = Geely2SyncTask.objects.create(
            user=self.user,
            credential_binding=self.binding,
            status='SUCCESS',
            message='同步完成',
        )
        Geely2IssueSnapshot.objects.create(
            user=self.user,
            last_sync_task=sync_task,
            issue_key='GEELY2-SSE-1',
            summary='首帧快照',
            jira_updated_at=timezone.now(),
        )

        response = self.client.get('/api/geely2/stream/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual(response['Cache-Control'], 'no-cache')
        self.assertEqual(response['X-Accel-Buffering'], 'no')

        first_chunk = next(iter(response.streaming_content))
        if isinstance(first_chunk, bytes):
            first_chunk = first_chunk.decode('utf-8')

        self.assertIn('event: geely2', first_chunk)
        self.assertIn('GEELY2-SSE-1', first_chunk)
        response.close()