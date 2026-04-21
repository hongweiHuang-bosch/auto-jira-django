from legacy_core.ai_client_by_langchain import AIClient
from legacy_core.jira_utils import JiraClient
from legacy_core.utils import load_config

from .credential_crypto import decrypt_secret


def build_jira_client(binding):
    return JiraClient(
        server=binding.jira_base_url,
        username=binding.jira_username,
        password=decrypt_secret(binding.encrypted_password),
    )


def build_ai_client():
    cfg = load_config('config.yaml')
    ai_cfg = cfg['ai']
    return AIClient(
        base_url=ai_cfg['base_url'],
        api_key=ai_cfg['api_key'],
        model=ai_cfg['model'],
        connect_timeout=ai_cfg.get('connect_timeout', 10),
        read_timeout=ai_cfg.get('read_timeout', 300),
        max_retries=ai_cfg.get('max_retries', 3),
        use_system_proxy=ai_cfg.get('use_system_proxy', False),
        proxies=ai_cfg.get('proxies'),
    )
