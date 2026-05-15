"""Encrypt legacy product installation credentials and clear plaintext fields.

Run from backend/ after applying migrations:

    PRODUCT_INSTALLATION_CREDENTIAL_KEY=... ./venv/bin/python scripts/encrypt_product_installation_credentials.py
"""

import asyncio

from sqlalchemy import select

from app.core.product_credential_crypto import encrypt_product_credential
from app.database import async_session_maker
from app.models.product_installation import ProductInstallation


async def main() -> None:
    async with async_session_maker() as db:
        result = await db.execute(select(ProductInstallation))
        installations = result.scalars().all()
        migrated = 0

        for installation in installations:
            changed = False
            for field in ("username", "password", "login_url"):
                plaintext = getattr(installation, field, None)
                ciphertext_field = f"{field}_ciphertext"
                ciphertext = getattr(installation, ciphertext_field, None)
                if plaintext and not ciphertext:
                    setattr(
                        installation,
                        ciphertext_field,
                        encrypt_product_credential(plaintext),
                    )
                    setattr(installation, field, None)
                    changed = True
                elif plaintext and ciphertext:
                    setattr(installation, field, None)
                    changed = True

            if changed:
                migrated += 1

        await db.commit()
        print(f"migrated={migrated}")


if __name__ == "__main__":
    asyncio.run(main())
