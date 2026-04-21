import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _build_fernet() -> Fernet:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(raw_value: str) -> str:
    return _build_fernet().encrypt(raw_value.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_value: str) -> str:
    return _build_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
