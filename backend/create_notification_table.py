import asyncio
from sqlalchemy import text
from app.database import engine


async def create_user_notification_table():
    async with engine.begin() as conn:
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS user_notification_reads (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                read_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, entity_type, entity_id, notification_type)
            )
        """)
        )
        print("User notification read table created successfully!")


if __name__ == "__main__":
    asyncio.run(create_user_notification_table())
