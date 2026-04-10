import asyncio
from sqlalchemy import select
from app.database import get_db
from app.models.user import User


async def check_users():
    async for db in get_db():
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(
                f"- ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}, Feishu ID: {u.feishu_id if u.feishu_id else 'None'}"
            )
        await db.close()


if __name__ == "__main__":
    asyncio.run(check_users())
