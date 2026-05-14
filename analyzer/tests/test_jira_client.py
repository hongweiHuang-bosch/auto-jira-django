from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from legacy_core.jira_utils import JiraClient


class JiraClientTests(SimpleTestCase):
    @patch('legacy_core.jira_utils.JIRA')
    def test_disables_env_proxy_when_configured(self, mock_jira_cls):
        mock_jira_cls.return_value = SimpleNamespace(_session=SimpleNamespace(trust_env=True))

        JiraClient(
            server='https://jira.example.com',
            username='tester',
            password='secret',
            use_system_proxy=False,
        )

        mock_jira_cls.assert_called_once_with(
            server='https://jira.example.com',
            basic_auth=('tester', 'secret'),
            get_server_info=False,
            proxies=None,
        )
        self.assertFalse(mock_jira_cls.return_value._session.trust_env)

    @patch('legacy_core.jira_utils.JIRA')
    def test_passes_explicit_proxies(self, mock_jira_cls):
        mock_jira_cls.return_value = SimpleNamespace(_session=SimpleNamespace(trust_env=True))
        proxies = {'https': 'http://proxy.example.com:8080'}

        JiraClient(
            server='https://jira.example.com',
            username='tester',
            password='secret',
            proxies=proxies,
        )

        mock_jira_cls.assert_called_once_with(
            server='https://jira.example.com',
            basic_auth=('tester', 'secret'),
            get_server_info=False,
            proxies=proxies,
        )