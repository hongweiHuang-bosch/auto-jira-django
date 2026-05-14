import json

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from geely2_analyzer.models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    JiraCredentialBinding,
)


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode('utf-8'))
class Geely2AnalysisApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_result_user',
            password='Geely2Pass123!',
        )
        self.client.force_login(self.user)
        self.binding = JiraCredentialBinding.objects.create(
            user=self.user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username='user@example.com',
            encrypted_password='jira-password',
        )
        self.snapshot = Geely2IssueSnapshot.objects.create(
            user=self.user,
            issue_key='GEELY2-120',
            summary='蓝牙异常',
            assignee='Xin SHEN',
        )

    def test_create_analysis_task_and_update_result(self):
        create_response = self.client.post('/api/geely2/issues/GEELY2-120/analysis-tasks/')
        self.assertEqual(create_response.status_code, 201)
        task = Geely2AnalysisTask.objects.get(issue_key='GEELY2-120')
        result = Geely2AnalysisResult.objects.create(
            analysis_task=task,
            user=self.user,
            issue_key='GEELY2-120',
            reply_text='初始回复',
        )
        update_response = self.client.patch(
            f'/api/geely2/analysis-results/{result.id}/',
            data=json.dumps({'reply_text': '更新后的回复'}),
            content_type='application/json',
        )
        self.assertEqual(update_response.status_code, 200)
        result.refresh_from_db()
        self.assertEqual(result.reply_text, '更新后的回复')

    def test_create_analysis_task_requires_credential_binding(self):
        """没有凭据绑定时创建分析任务应返回 404。"""
        self.binding.delete()
        create_response = self.client.post('/api/geely2/issues/GEELY2-120/analysis-tasks/')
        self.assertEqual(create_response.status_code, 404)

    def test_create_analysis_task_rejects_duplicate_active(self):
        """已有活跃分析任务时，创建第二个应返回 409。"""
        self.client.post('/api/geely2/issues/GEELY2-120/analysis-tasks/')
        dup_response = self.client.post('/api/geely2/issues/GEELY2-120/analysis-tasks/')
        self.assertEqual(dup_response.status_code, 409)
