"""
Database connection and session management with production-grade connection pooling.
"""

import logging
import random
import time
from typing import Generator

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_database_engine():
    """Create database engine with production-grade configuration and retry logic."""

    # Production-grade engine configuration
    engine_config = {
        "poolclass": QueuePool,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        "pool_recycle": settings.DATABASE_POOL_RECYCLE,
        "pool_pre_ping": settings.DATABASE_POOL_PRE_PING,
        "echo": settings.DATABASE_ECHO,
        "connect_args": {
            "connect_timeout": settings.DATABASE_CONNECT_TIMEOUT,
            "application_name": f"OriginFD-API-{settings.ENVIRONMENT}",
            # Enable prepared statements for better performance
            "options": "-c default_transaction_isolation=read committed",
        },
    }

    # Create engine with retry logic
    max_retries = settings.DATABASE_RETRY_ATTEMPTS
    for attempt in range(max_retries):
        try:
            engine = create_engine(settings.DATABASE_URL, **engine_config)

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(f"Database engine created successfully (attempt {attempt + 1})")
            return engine

        except (OperationalError, DisconnectionError) as e:
            if attempt == max_retries - 1:
                logger.error(
                    f"Failed to create database engine after {max_retries} attempts: {e}"
                )
                raise

            # Exponential backoff with jitter
            delay = settings.DATABASE_RETRY_DELAY * (2**attempt) + random.uniform(0, 1)
            logger.warning(
                f"Database connection attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
            )
            time.sleep(delay)


# Create database engine with retry logic
engine = create_database_engine()


# Add connection event listeners for monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log successful database connections."""
    logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection pool checkouts."""
    logger.debug(
        f"Connection checked out from pool. Pool size: {engine.pool.size()}, Checked out: {engine.pool.checkedout()}"
    )


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection pool checkins."""
    logger.debug("Connection returned to pool")


@event.listens_for(engine, "invalidate")
def receive_invalidate(dbapi_connection, connection_record, exception):
    """Log connection invalidations."""
    logger.warning(f"Database connection invalidated: {exception}")


# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
        db.execute(
            text("SET app.current_tenant = :tenant_id"), {"tenant_id": tenant_id}
        )
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


def create_tables():
    """Create all database tables"""
    from models.base import Base

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


def init_database():
    """Initialize database with initial data"""
    create_tables()

    # Import models to ensure they're registered
    from models.project import Project
    from models.user import User

    # Create initial users
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@originfd.com").first()
        if not admin_user:
            from core.auth import get_password_hash

            admin_user = User(
                email="admin@originfd.com",
                hashed_password=get_password_hash("admin"),
                full_name="Admin User",
                is_active=True,
                is_verified=True,
                is_superuser=True,
                role="engineer",
            )
            db.add(admin_user)

            regular_user = User(
                email="user@originfd.com",
                hashed_password=get_password_hash("password"),
                full_name="Regular User",
                is_active=True,
                is_verified=True,
                is_superuser=False,
                role="user",
            )
            db.add(regular_user)

            db.commit()
            logger.info("Initial users created!")

            # Create sample projects
            from models.project import ProjectDomain, ProjectScale, ProjectStatus

            sample_projects = [
                Project(
                    name="Solar Farm Arizona Phase 1",
                    description="Large-scale solar PV installation in Arizona",
                    owner_id=admin_user.id,
                    domain=ProjectDomain.PV,
                    scale=ProjectScale.UTILITY,
                    status=ProjectStatus.ACTIVE,
                    location_name="Arizona, USA",
                    total_capacity_kw=500000.0,
                ),
                Project(
                    name="Commercial BESS Installation",
                    description="Battery energy storage system for commercial building",
                    owner_id=admin_user.id,
                    domain=ProjectDomain.BESS,
                    scale=ProjectScale.COMMERCIAL,
                    status=ProjectStatus.DRAFT,
                    location_name="California, USA",
                    total_capacity_kw=2000.0,
                ),
                Project(
                    name="Hybrid Microgrid Campus",
                    description="Combined PV + BESS system for university campus",
                    owner_id=regular_user.id,
                    domain=ProjectDomain.HYBRID,
                    scale=ProjectScale.INDUSTRIAL,
                    status=ProjectStatus.UNDER_REVIEW,
                    location_name="Texas, USA",
                    total_capacity_kw=10000.0,
                ),
            ]

            for project in sample_projects:
                db.add(project)

            db.commit()
            logger.info("Sample projects created!")
        else:
            logger.info("Database already initialized!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        db.close()
