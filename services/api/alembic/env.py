"""
Alembic environment configuration for OriginFD database migrations.
"""

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure repository root is on sys.path so packages import cleanly
try:
    from tools.paths import ensure_repo_on_path  # type: ignore
except ModuleNotFoundError:  # pragma: no cover

    def ensure_repo_on_path() -> None:
        root = Path(__file__).resolve().parents[3]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))


ensure_repo_on_path()

from core.config import get_settings  # noqa: E402

from services.api.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Add model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()
database_url = os.getenv("DATABASE_URL", settings.get_database_url())
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            # Enable PostgreSQL extensions if using PostgreSQL
            from sqlalchemy import text

            if connection.dialect.name == "postgresql":
                connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

                # Enable Row Level Security on tables that need it
                connection.execute(
                    text("ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY")
                )
                connection.execute(
                    text(
                        "ALTER TABLE IF EXISTS document_versions "
                        "ENABLE ROW LEVEL SECURITY"
                    )
                )
                connection.execute(
                    text(
                        "ALTER TABLE IF EXISTS document_access "
                        "ENABLE ROW LEVEL SECURITY"
                    )
                )
                connection.execute(
                    text("ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY")
                )

            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
