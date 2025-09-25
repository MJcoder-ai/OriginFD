import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from services.api.domain.lifecycle_catalog import LIFECYCLE_CATALOG
from services.api.domain.lifecycle_view import build_lifecycle_view
from services.api.models import (
    Base,
    LifecycleGate,
    LifecyclePhase,
)
from services.api.models.project import Project
from services.api.models.project import ProjectDomain
from services.api.models.project import ProjectScale
from services.api.models.project import ProjectStatus
from services.api.models.user import User
from services.api.models.lifecycle import GateStatus
from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        User.__table__,
        Project.__table__,
        LifecyclePhase.__table__,
        LifecycleGate.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=tables)


def _create_project(session: Session) -> Project:
    user = User(
        email="view-builder@originfd.com",
        hashed_password="test-hash",
        full_name="Lifecycle Viewer",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="pm",
    )
    session.add(user)
    session.flush()

    project = Project(
        name="Lifecycle View",
        description="",
        domain=ProjectDomain.PV,
        scale=ProjectScale.UTILITY,
        status=ProjectStatus.DRAFT,
        owner_id=user.id,
    )
    session.add(project)
    session.flush()
    return project


def test_build_lifecycle_view_from_database(db_session: Session) -> None:
    project = _create_project(db_session)
    seed_lifecycle_catalog(db_session, project=project)
    db_session.commit()

    # Promote one entry gate to IN_PROGRESS
    phase = db_session.execute(
        select(LifecyclePhase).where(
            LifecyclePhase.project_id == project.id,
            LifecyclePhase.phase_code == 4,
        )
    ).scalar_one()

    entry_gate = LifecycleGate(
        project_id=project.id,
        phase_id=phase.id,
        phase_code=phase.phase_code,
        gate_code=phase.entry_gate_code,
        name=f"{phase.entry_gate_code} Entry",
        description=None,
        sequence=1,
        status=GateStatus.IN_PROGRESS,
    )
    db_session.add(entry_gate)
    db_session.commit()

    view = build_lifecycle_view(db_session, project.id)

    assert len(view) == len(LIFECYCLE_CATALOG)
    assert [phase["phase_code"] for phase in view] == list(range(len(LIFECYCLE_CATALOG)))

    for phase_payload in view:
        assert "phase_code" in phase_payload
        assert "entry_gate_code" in phase_payload
        assert "exit_gate_code" in phase_payload
        assert isinstance(phase_payload.get("required_entry_roles"), list)
        assert isinstance(phase_payload.get("required_exit_roles"), list)
        assert isinstance(phase_payload.get("odl_sd_sections"), list)
        gates = phase_payload.get("gates", [])
        assert len(gates) == 2
        for gate_payload in gates:
            assert gate_payload.get("gate_code")
            assert gate_payload.get("status")

    target_phase = next(
        phase_payload for phase_payload in view if phase_payload["phase_code"] == phase.phase_code
    )
    entry_payload = next(
        gate_payload
        for gate_payload in target_phase["gates"]
        if gate_payload["gate_code"] == phase.entry_gate_code
    )
    assert entry_payload["status"] == GateStatus.IN_PROGRESS.value

    exit_payload = next(
        gate_payload
        for gate_payload in target_phase["gates"]
        if gate_payload["gate_code"] == phase.exit_gate_code
    )
    assert exit_payload["status"] == GateStatus.NOT_STARTED.value

    first_phase = next(
        phase_payload for phase_payload in view if phase_payload["phase_code"] == 0
    )
    first_entry = next(
        gate_payload
        for gate_payload in first_phase["gates"]
        if gate_payload["gate_code"] == first_phase["entry_gate_code"]
    )
    assert first_entry["status"] == GateStatus.NOT_STARTED.value
