from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
import os

# 统一从配置获取数据库URL
from app.core.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def init_db():
    app_env = os.getenv("APP_ENV", "").lower()
    is_test_env = app_env in {"test", "testing"} or "PYTEST_CURRENT_TEST" in os.environ
    if not is_test_env:
        raise RuntimeError(
            "init_db/create_all is restricted to test environments. Use Alembic migrations instead."
        )

    async with engine.begin() as conn:
        from app.models import Base as models_base

        await conn.run_sync(models_base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
