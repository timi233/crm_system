"""Minimal Alembic environment for current DB schema."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import sys
import os

# Add the parent directory to path to import models correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

config = context.config
fileConfig(config.config_file_name)

# Import the actual models' metadata
from app.models import Base

target_metadata = Base.metadata


def get_database_url():
    """Get database URL from settings or environment variable."""
    try:
        # Try to import and use Settings first
        from app.core.config import get_settings

        settings = get_settings()
        return settings.database_url
    except (ImportError, AttributeError, ValueError):
        # Fallback to environment variable if settings not available
        return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    url = get_database_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
