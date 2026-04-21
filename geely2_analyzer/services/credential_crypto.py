import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _build_fernet() -> Fernet:
    encryption_key = getattr(settings, 'JIRA_CREDENTIAL_ENCRYPTION_KEY', '')
    if encryption_key:
        return Fernet(encryption_key.encode('utf-8'))

    if settings.DEBUG:
        digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    raise ImproperlyConfigured(
        'JIRA_CREDENTIAL_ENCRYPTION_KEY must be set when DEBUG is False.'
    )


def encrypt_secret(raw_value: str) -> str:
    return _build_fernet().encrypt(raw_value.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_value: str) -> str:
    return _build_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
