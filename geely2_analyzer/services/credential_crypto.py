from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


ENCRYPTED_SECRET_PREFIX = 'enc::'


def _build_fernet() -> Fernet:
    encryption_key = getattr(settings, 'JIRA_CREDENTIAL_ENCRYPTION_KEY', '')
    if encryption_key:
        return Fernet(encryption_key.encode('utf-8'))

    raise ImproperlyConfigured('JIRA_CREDENTIAL_ENCRYPTION_KEY must be set.')


def is_encrypted_secret(value: str) -> bool:
    return value.startswith(ENCRYPTED_SECRET_PREFIX)


def encrypt_secret(raw_value: str) -> str:
    token = _build_fernet().encrypt(raw_value.encode("utf-8")).decode("utf-8")
    return f'{ENCRYPTED_SECRET_PREFIX}{token}'


def decrypt_secret(encrypted_value: str) -> str:
    token = encrypted_value
    if is_encrypted_secret(encrypted_value):
        token = encrypted_value[len(ENCRYPTED_SECRET_PREFIX):]
    return _build_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
