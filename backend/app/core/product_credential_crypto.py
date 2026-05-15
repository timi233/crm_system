import base64
import hashlib
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from app.core.config import get_settings


def _derive_fernet_key(raw_key: str) -> bytes:
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache
def _get_fernet() -> Fernet:
    settings = get_settings()
    raw_key = settings.product_installation_credential_key
    if not raw_key:
        raise HTTPException(
            status_code=500,
            detail="PRODUCT_INSTALLATION_CREDENTIAL_KEY is not configured",
        )
    if len(raw_key) < 32:
        raise HTTPException(
            status_code=500,
            detail="PRODUCT_INSTALLATION_CREDENTIAL_KEY must be at least 32 chars",
        )
    return Fernet(_derive_fernet_key(raw_key))


def encrypt_product_credential(value: Optional[str]) -> Optional[str]:
    if value in (None, ""):
        return None
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_product_credential(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(status_code=500, detail="产品装机凭据解密失败") from exc
