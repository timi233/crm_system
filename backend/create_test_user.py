import asyncio
import bcrypt
from sqlalchemy import select
from app.database import get_db, engine
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_test_user():
    # First check if user already exists
    async for db in get_db():
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User already exists: {existing.name}")
            return

        # Create new user
        password_hash = bcrypt.hashpw(
            "admin123".encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        new_user = User(
            name="Admin User",
            email="admin@example.com",
            hashed_password=password_hash,
            role="admin",
            is_active=True,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print(
            f"Created test user: {new_user.name} (email: admin@example.com, password: admin123)"
        )
        await db.close()


if __name__ == "__main__":
    asyncio.run(create_test_user())
