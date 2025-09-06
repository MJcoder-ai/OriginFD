"""
Database connection and session management.
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for models
Base = declarative_base()

# Metadata for schema generation
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Create database session with proper cleanup.
    Use as FastAPI dependency.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_with_tenant(tenant_id: str) -> Generator[Session, None, None]:
    """
    Create database session with tenant context for RLS.
    """
    db = SessionLocal()
    try:
        # Set tenant context for Row Level Security
        db.execute(text("SET app.current_tenant = :tenant_id"), {"tenant_id": tenant_id})
        yield db
    except Exception as e:
        logger.error(f"Database session error for tenant {tenant_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def check_database_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Type hint for dependency injection
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[Session, Depends(get_db)]