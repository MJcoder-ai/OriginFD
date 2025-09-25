import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from services.api.domain.lifecycle_catalog import LIFECYCLE_CATALOG
from services.api.domain.lifecycle_service import (
    ForbiddenApprovalError,
    update_gate_status,
)
from services.api.models import (
    Base,
    LifecycleGate,
    LifecycleGateApproval,
    LifecyclePhase,
)
from services.api.models.project import Project
from services.api.models.project import ProjectDomain
from services.api.models.project import ProjectScale
from services.api.models.project import ProjectStatus
from services.api.models.user import User
from services.api.models.lifecycle import ApprovalDecision, GateStatus
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


def _create_project(session: Session) -> tuple[Project, User]:
    user = User(
        email="gate-updates@originfd.com",
        hashed_password="test-hash",
        full_name="Lifecycle Approver",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="engineer",
    )
    session.add(user)
    session.flush()

    project = Project(
        name="Lifecycle Service",
        description="",
        domain=ProjectDomain.PV,
        scale=ProjectScale.UTILITY,
        status=ProjectStatus.DRAFT,
        owner_id=user.id,
    )
    session.add(project)
    session.flush()
    return project, user


def _phase_spec(code: int):
    return next(spec for spec in LIFECYCLE_CATALOG if spec.phase_code == code)


def test_update_gate_status_approves_entry_gate(db_session: Session) -> None:
    project, user = _create_project(db_session)
    seed_lifecycle_catalog(db_session, project=project)
    db_session.flush()

    phase_code = 0
    spec = _phase_spec(phase_code)
    gate, approval = update_gate_status(
        db_session,
        project_id=project.id,
        phase_code=phase_code,
        gate_code=spec.entry_gate_code,
        decision=ApprovalDecision.APPROVE,
        role_key=spec.required_entry_roles[0],
        approver_user_id=user.id,
        comment="approved",
    )
    db_session.flush()

    stored_gate = db_session.execute(
        select(LifecycleGate).where(
            LifecycleGate.project_id == project.id,
            LifecycleGate.phase_code == phase_code,
            LifecycleGate.gate_code == spec.entry_gate_code,
        )
    ).scalar_one()
    assert stored_gate.status == GateStatus.APPROVED
    assert stored_gate.sequence == 1

    approvals = db_session.execute(
        select(LifecycleGateApproval).where(
            LifecycleGateApproval.gate_id == stored_gate.id,
        )
    ).scalars().all()
    assert len(approvals) == 1
    assert approvals[0].decision == ApprovalDecision.APPROVE
    assert approvals[0].role_key == spec.required_entry_roles[0]


def test_update_gate_status_rejects_entry_gate(db_session: Session) -> None:
    project, user = _create_project(db_session)
    seed_lifecycle_catalog(db_session, project=project)
    db_session.flush()

    phase_code = 2
    spec = _phase_spec(phase_code)
    update_gate_status(
        db_session,
        project_id=project.id,
        phase_code=phase_code,
        gate_code=spec.entry_gate_code,
        decision=ApprovalDecision.REJECT,
        role_key=spec.required_entry_roles[0],
        approver_user_id=user.id,
        comment="needs work",
    )
    db_session.flush()

    stored_gate = db_session.execute(
        select(LifecycleGate).where(
            LifecycleGate.project_id == project.id,
            LifecycleGate.phase_code == phase_code,
            LifecycleGate.gate_code == spec.entry_gate_code,
        )
    ).scalar_one()
    assert stored_gate.status == GateStatus.REJECTED


def test_update_gate_status_requires_authorized_role(db_session: Session) -> None:
    project, user = _create_project(db_session)
    seed_lifecycle_catalog(db_session, project=project)
    db_session.flush()

    spec = _phase_spec(0)
    with pytest.raises(ForbiddenApprovalError):
        update_gate_status(
            db_session,
            project_id=project.id,
            phase_code=0,
            gate_code=spec.entry_gate_code,
            decision=ApprovalDecision.APPROVE,
            role_key="role.unauthorized",
            approver_user_id=user.id,
        )


def test_update_gate_status_handles_exit_gate(db_session: Session) -> None:
    project, user = _create_project(db_session)
    seed_lifecycle_catalog(db_session, project=project)
    db_session.flush()

    phase_code = 9
    spec = _phase_spec(phase_code)
    update_gate_status(
        db_session,
        project_id=project.id,
        phase_code=phase_code,
        gate_code=spec.exit_gate_code,
        decision=ApprovalDecision.APPROVE,
        role_key=spec.required_exit_roles[0],
        approver_user_id=user.id,
    )
    db_session.flush()

    stored_gate = db_session.execute(
        select(LifecycleGate).where(
            LifecycleGate.project_id == project.id,
            LifecycleGate.phase_code == phase_code,
            LifecycleGate.gate_code == spec.exit_gate_code,
        )
    ).scalar_one()
    assert stored_gate.status == GateStatus.APPROVED
    assert stored_gate.sequence == 2

    approval = db_session.execute(
        select(LifecycleGateApproval).where(
            LifecycleGateApproval.gate_id == stored_gate.id,
        )
    ).scalar_one()
    assert approval.decision == ApprovalDecision.APPROVE
