import asyncio
from sqlalchemy import text
from app.database import engine


async def create_alerts_table():
    async with engine.begin() as conn:
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id SERIAL PRIMARY KEY,
                rule_code VARCHAR(50) UNIQUE NOT NULL,
                rule_name VARCHAR(100) NOT NULL,
                rule_type VARCHAR(30) NOT NULL,
                entity_type VARCHAR(30) NOT NULL,
                priority VARCHAR(10) NOT NULL DEFAULT 'medium',
                threshold_days INTEGER DEFAULT 0,
                threshold_amount INTEGER DEFAULT 0,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at VARCHAR(30),
                updated_at VARCHAR(30)
            )
        """)
        )
        print("Alert rules table created successfully!")


if __name__ == "__main__":
    asyncio.run(create_alerts_table())
