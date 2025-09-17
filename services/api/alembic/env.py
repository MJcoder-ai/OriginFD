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

# Add the parent directory to Python path to import models
sys.path.append(str(Path(__file__).parent.parent))

import models.component
import models.document
import models.project

# Import all models to ensure they're registered with Base
import models.tenant
import models.user
from core.config import get_settings
from models.base import Base

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
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


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
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

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
                        "ALTER TABLE IF EXISTS document_versions ENABLE ROW LEVEL SECURITY"
                    )
                )
                connection.execute(
                    text(
                        "ALTER TABLE IF EXISTS document_access ENABLE ROW LEVEL SECURITY"
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
