import pytest

from app.core.config import get_settings
from app.core.product_credential_crypto import (
    _get_fernet,
    decrypt_product_credential,
    encrypt_product_credential,
)
from app.models.product_installation import ProductInstallation
from app.routers.product_installation import (
    get_plain_credential,
    mask_credential,
    set_encrypted_credential,
)


pytestmark = pytest.mark.asyncio


def _reset_crypto_settings(monkeypatch):
    monkeypatch.setenv(
        "PRODUCT_INSTALLATION_CREDENTIAL_KEY",
        "test_product_installation_credential_key_32_chars",
    )
    get_settings.cache_clear()
    _get_fernet.cache_clear()


async def test_product_installation_credentials_encrypt_and_decrypt(monkeypatch):
    _reset_crypto_settings(monkeypatch)

    ciphertext = encrypt_product_credential("secret-password")

    assert ciphertext
    assert ciphertext != "secret-password"
    assert decrypt_product_credential(ciphertext) == "secret-password"


async def test_product_installation_router_helpers_store_ciphertext(monkeypatch):
    _reset_crypto_settings(monkeypatch)
    installation = ProductInstallation(id=1, customer_id=1)

    set_encrypted_credential(installation, "password", "secret-password")

    assert installation.password is None
    assert installation.password_ciphertext
    assert installation.password_ciphertext != "secret-password"
    assert mask_credential(installation, "password") == "******"
    assert get_plain_credential(installation, "password") == "secret-password"


async def test_product_installation_legacy_plaintext_read_fallback(monkeypatch):
    _reset_crypto_settings(monkeypatch)
    installation = ProductInstallation(id=1, customer_id=1, username="legacy-user")

    assert mask_credential(installation, "username") == "******"
    assert get_plain_credential(installation, "username") == "legacy-user"
