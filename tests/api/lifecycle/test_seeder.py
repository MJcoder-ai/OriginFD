import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from services.api.domain.lifecycle_catalog import LIFECYCLE_CATALOG
from services.api.models import (
    Base,
    LifecyclePhase,
)
from services.api.models.project import Project
from services.api.models.project import ProjectDomain
from services.api.models.project import ProjectScale
from services.api.models.project import ProjectStatus
from services.api.models.user import User
from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _create_project(session: Session) -> Project:
    user = User(
        email="catalog-tester@originfd.com",
        hashed_password="test-hash",
        full_name="Catalog Tester",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="engineer",
    )
    session.add(user)
    session.flush()

    project = Project(
        name="Catalog Project",
        description="",
        domain=ProjectDomain.PV,
        scale=ProjectScale.UTILITY,
        status=ProjectStatus.DRAFT,
        owner_id=user.id,
    )
    session.add(project)
    session.flush()
    return project


def test_lifecycle_catalog_seeder_is_idempotent(db_session: Session) -> None:
    project = _create_project(db_session)
    db_session.commit()

    first = seed_lifecycle_catalog(db_session, project=project)
    db_session.commit()

    second = seed_lifecycle_catalog(db_session, project=project)
    db_session.commit()

    # First run should insert everything; second run should be unchanged
    assert first["inserted"] == len(LIFECYCLE_CATALOG)
    assert first["updated"] == 0
    assert second["updated"] == 0
    assert second["unchanged"] == len(LIFECYCLE_CATALOG)

    phases = db_session.scalars(
        select(LifecyclePhase).where(LifecyclePhase.project_id == project.id)
    ).all()
    assert len(phases) == len(LIFECYCLE_CATALOG)

    # check a couple of representative specs by phase_code (first and last)
    catalog_by_code = {spec.phase_code: spec for spec in LIFECYCLE_CATALOG}
    for phase in phases:
        spec = catalog_by_code[phase.phase_code]
        assert phase.phase_key == spec.phase_key
        assert phase.title == spec.title
        assert phase.sequence == spec.order
