import asyncio
from sqlalchemy import text
from app.database import engine


async def create_missing_tables():
    async with engine.begin() as conn:
        # Create sales_targets table
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS sales_targets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                target_type VARCHAR(20) NOT NULL,
                target_year INTEGER NOT NULL,
                target_period INTEGER NOT NULL,
                target_amount FLOAT NOT NULL,
                parent_id INTEGER REFERENCES sales_targets(id),
                created_at DATE,
                updated_at DATE
            )
        """)
        )

        # Create alerts table (if needed)
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'info',
                title VARCHAR(255) NOT NULL,
                message TEXT,
                entity_type VARCHAR(50),
                entity_id INTEGER,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT NOW(),
                is_read BOOLEAN DEFAULT FALSE,
                read_at TIMESTAMP
            )
        """)
        )

        print("Missing tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_missing_tables())
