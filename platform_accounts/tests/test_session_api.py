import base64
import json

from django.contrib.auth import get_user_model
from django.test import TestCase


class SessionApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='geely_user',
            password='Geely2Pass123!'
        )

    def test_login_me_logout_flow(self):
        csrf_response = self.client.get('/api/platform/csrf/')
        self.assertEqual(csrf_response.status_code, 204)

        login_response = self.client.post(
            '/api/platform/login/',
            data=json.dumps({'username': 'geely_user', 'password': 'Geely2Pass123!'}),
            content_type='application/json',
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()['username'], 'geely_user')

        me_response = self.client.get('/api/platform/session/')
        self.assertEqual(me_response.status_code, 200)
        self.assertTrue(me_response.json()['authenticated'])

        logout_response = self.client.post('/api/platform/logout/')
        self.assertEqual(logout_response.status_code, 200)

        me_after_logout = self.client.get('/api/platform/session/')
        self.assertEqual(me_after_logout.status_code, 401)

    def test_protected_endpoints_require_session_auth(self):
        credentials = base64.b64encode(b'geely_user:Geely2Pass123!').decode()

        session_response = self.client.get(
            '/api/platform/session/',
            HTTP_AUTHORIZATION=f'Basic {credentials}',
        )
        self.assertEqual(session_response.status_code, 401)

        logout_response = self.client.post(
            '/api/platform/logout/',
            HTTP_AUTHORIZATION=f'Basic {credentials}',
        )
        self.assertEqual(logout_response.status_code, 401)