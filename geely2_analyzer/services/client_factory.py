from legacy_core.jira_utils import JiraClient

from .credential_crypto import decrypt_secret


def build_jira_client(binding):
    return JiraClient(
        server=binding.jira_base_url,
        username=binding.jira_username,
        password=decrypt_secret(binding.encrypted_password),
    )
