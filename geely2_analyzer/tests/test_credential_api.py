import json

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from geely2_analyzer.models import JiraCredentialBinding
from geely2_analyzer.services.credential_crypto import decrypt_secret


@override_settings(JIRA_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode('utf-8'))
class Geely2CredentialApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='geely_api_user',
            password='Geely2Pass123!',
        )
        self.other_user = user_model.objects.create_user(
            username='other_geely_user',
            password='Geely2Pass123!',
        )
        self.client.force_login(self.user)

    def _create_binding(self, user, username='existing@example.com', password='Secret987!'):
        return JiraCredentialBinding.objects.create(
            user=user,
            project_code='geely2',
            jira_base_url='https://boolbool.atlassian.net/',
            jira_username=username,
            encrypted_password=password,
            is_active=True,
        )

    def test_credential_endpoint_requires_session_authentication(self):
        response = Client().get('/api/geely2/credential/')

        self.assertEqual(response.status_code, 401)

    def test_get_returns_unconfigured_when_binding_missing(self):
        response = self.client.get('/api/geely2/credential/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'configured': False})

    def test_put_and_get_credential_binding(self):
        put_response = self.client.put(
            '/api/geely2/credential/',
            data=json.dumps(
                {
                    'jira_base_url': 'https://boolbool.atlassian.net/',
                    'jira_username': 'xin.shen@example.com',
                    'jira_password': 'Secret987!',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json()['configured'], True)
        self.assertNotIn('encrypted_password', put_response.json())

        binding = JiraCredentialBinding.objects.get(user=self.user, project_code='geely2')
        self.assertEqual(binding.jira_username, 'xin.shen@example.com')
        self.assertEqual(decrypt_secret(binding.encrypted_password), 'Secret987!')

        get_response = self.client.get('/api/geely2/credential/')

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()['configured'], True)
        self.assertEqual(get_response.json()['jira_username'], 'xin.shen@example.com')
        self.assertNotIn('encrypted_password', get_response.json())
        self.assertNotIn('jira_password', get_response.json())

    def test_put_updates_only_current_user_binding(self):
        self._create_binding(self.user, username='before@example.com', password='Before123!')
        other_binding = self._create_binding(
            self.other_user,
            username='other@example.com',
            password='Other123!',
        )

        response = self.client.put(
            '/api/geely2/credential/',
            data=json.dumps(
                {
                    'jira_base_url': 'https://boolbool.atlassian.net/',
                    'jira_username': 'after@example.com',
                    'jira_password': 'After123!',
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)

        current_binding = JiraCredentialBinding.objects.get(user=self.user, project_code='geely2')
        other_binding.refresh_from_db()

        self.assertEqual(current_binding.jira_username, 'after@example.com')
        self.assertEqual(decrypt_secret(current_binding.encrypted_password), 'After123!')
        self.assertEqual(other_binding.jira_username, 'other@example.com')
        self.assertEqual(decrypt_secret(other_binding.encrypted_password), 'Other123!')