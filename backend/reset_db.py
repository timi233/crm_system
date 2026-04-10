import asyncio
from app.database import drop_db, init_db


async def reset_database():
    await drop_db()
    await init_db()
    print("Database schema reset completed!")


if __name__ == "__main__":
    asyncio.run(reset_database())
