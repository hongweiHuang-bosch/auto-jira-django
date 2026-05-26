from unittest.mock import patch

from django.test import SimpleTestCase

from analyzer.services.feishu_notifier import get_feishu_webhook_url


class FeishuNotifierTests(SimpleTestCase):
    @patch.dict('os.environ', {}, clear=True)
    @patch('analyzer.services.feishu_notifier.load_config', return_value={'feishu.webhook_url': 'https://example.test/hook'})
    def test_get_feishu_webhook_url_supports_flat_config_key(self, _mock_load_config):
        self.assertEqual(get_feishu_webhook_url(), 'https://example.test/hook')