from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _build_fernet() -> Fernet:
    encryption_key = getattr(settings, 'JIRA_CREDENTIAL_ENCRYPTION_KEY', '')
    if encryption_key:
        return Fernet(encryption_key.encode('utf-8'))

    raise ImproperlyConfigured('JIRA_CREDENTIAL_ENCRYPTION_KEY must be set.')


def encrypt_secret(raw_value: str) -> str:
    return _build_fernet().encrypt(raw_value.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_value: str) -> str:
    return _build_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
