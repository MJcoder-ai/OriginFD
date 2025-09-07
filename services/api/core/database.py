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
    from models.user import User
    from models.project import Project
    
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
                role="engineer"
            )
            db.add(admin_user)
            
            regular_user = User(
                email="user@originfd.com",
                hashed_password=get_password_hash("password"),
                full_name="Regular User", 
                is_active=True,
                is_verified=True,
                is_superuser=False,
                role="user"
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
                    total_capacity_kw="500000"
                ),
                Project(
                    name="Commercial BESS Installation",
                    description="Battery energy storage system for commercial building",
                    owner_id=admin_user.id,
                    domain=ProjectDomain.BESS,
                    scale=ProjectScale.COMMERCIAL,
                    status=ProjectStatus.DRAFT,
                    location_name="California, USA",
                    total_capacity_kw="2000"
                ),
                Project(
                    name="Hybrid Microgrid Campus",
                    description="Combined PV + BESS system for university campus",
                    owner_id=regular_user.id,
                    domain=ProjectDomain.HYBRID,
                    scale=ProjectScale.INDUSTRIAL,
                    status=ProjectStatus.UNDER_REVIEW,
                    location_name="Texas, USA",
                    total_capacity_kw="10000"
                )
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