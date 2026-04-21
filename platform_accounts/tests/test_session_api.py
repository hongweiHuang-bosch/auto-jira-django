import base64
import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class SessionApiTests(TestCase):
    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            username='geely_user',
            password='Geely2Pass123!'
        )

    def test_login_me_logout_flow(self):
        csrf_response = self.csrf_client.get('/api/platform/csrf/')
        self.assertEqual(csrf_response.status_code, 204)
        csrf_token = self.csrf_client.cookies['csrftoken'].value

        login_response = self.csrf_client.post(
            '/api/platform/login/',
            data=json.dumps({'username': 'geely_user', 'password': 'Geely2Pass123!'}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()['username'], 'geely_user')

        me_response = self.csrf_client.get('/api/platform/session/')
        self.assertEqual(me_response.status_code, 200)
        self.assertTrue(me_response.json()['authenticated'])

        logout_response = self.csrf_client.post(
            '/api/platform/logout/',
            HTTP_X_CSRFTOKEN=self.csrf_client.cookies['csrftoken'].value,
        )
        self.assertEqual(logout_response.status_code, 200)

        me_after_logout = self.csrf_client.get('/api/platform/session/')
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

    def test_login_requires_csrf_token(self):
        response = self.csrf_client.post(
            '/api/platform/login/',
            data=json.dumps({'username': 'geely_user', 'password': 'Geely2Pass123!'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_logout_requires_csrf_token(self):
        self.csrf_client.get('/api/platform/csrf/')
        login_response = self.csrf_client.post(
            '/api/platform/login/',
            data=json.dumps({'username': 'geely_user', 'password': 'Geely2Pass123!'}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=self.csrf_client.cookies['csrftoken'].value,
        )
        self.assertEqual(login_response.status_code, 200)

        response = self.csrf_client.post('/api/platform/logout/')

        self.assertEqual(response.status_code, 403)