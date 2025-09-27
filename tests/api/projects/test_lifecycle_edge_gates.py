import uuid
import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("jwt-secret-key", "test-secret-key")
from services.api.core.config import get_settings
get_settings.cache_clear()
from types import SimpleNamespace
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT / "services"))
sys.path.append(str(ROOT / "services" / "api"))

models_module = importlib.import_module("services.api.models")
sys.modules.setdefault("models", models_module)
sys.modules.setdefault("core", importlib.import_module("services.api.core"))

for name, module in list(sys.modules.items()):
    if name.startswith("services.api.models"):
        alias = name.replace("services.api.models", "models", 1)
        sys.modules.setdefault(alias, module)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from services.api.api.routers.auth import create_access_token
from services.api.main import app
from services.api.models import (
    LifecycleGate,
    LifecycleGateApproval,
    LifecyclePhase,
)
from services.api.models.project import Project
from services.api.models.project import ProjectDomain
from services.api.models.project import ProjectScale
from services.api.models.project import ProjectStatus
from services.api.models.user import User
from services.api.models.lifecycle import GateStatus
from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog
from tests.api._utils.sqlite_harness import (
    create_tables,
    drop_tables,
    make_sqlite_engine,
    session_factory,
)


@pytest.fixture()
def edge_gate_env():
    engine = make_sqlite_engine()
    tables = [
        User.__table__,
        Project.__table__,
        LifecyclePhase.__table__,
        LifecycleGate.__table__,
        LifecycleGateApproval.__table__,
    ]
    create_tables(engine, tables)
    SessionLocal = session_factory(engine)

    with SessionLocal() as seed_session:
        user = _create_user(seed_session)
        project = _create_project(seed_session, user.id)
        seed_lifecycle_catalog(seed_session, project=project)
        seed_session.commit()
        user_id = user.id
        project_id = project.id

    current_user_state = {
        "id": str(user_id),
        "tenant_id": str(uuid.uuid4()),
        "roles": ["project_manager", "engineer", "approver"],
    }

    def override_get_db():
        db: Session = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    def _apply_roles(roles: list[str]) -> None:
        current_user_state["roles"] = roles
        token = create_access_token(
            {
                "sub": current_user_state["id"],
                "roles": roles,
                "tenant_id": current_user_state["tenant_id"],
            }
        )
        client.headers["Authorization"] = f"Bearer {token}"

    _apply_roles(current_user_state["roles"])

    def set_roles(roles: list[str]) -> None:
        _apply_roles(roles)

    try:
        yield SimpleNamespace(
            client=client,
            SessionLocal=SessionLocal,
            project_id=str(project_id),
            set_roles=set_roles,
        )
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)
        drop_tables(engine, tables)
        engine.dispose()


@pytest.fixture()
def client(edge_gate_env):
    return edge_gate_env.client


@pytest.fixture()
def project_id(edge_gate_env):
    return edge_gate_env.project_id


@pytest.fixture()
def set_roles(edge_gate_env):
    return edge_gate_env.set_roles


@pytest.fixture()
def session(edge_gate_env):
    db = edge_gate_env.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_user(session: Session) -> User:
    user = User(
        email="edge-gates@originfd.com",
        hashed_password="test-hash",
        full_name="Edge Gate Tester",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="project_manager",
    )
    user.id = uuid.uuid4()
    session.add(user)
    session.flush()
    return user


def _create_project(session: Session, owner_id) -> Project:
    project = Project(
        name="Edge Gate Lifecycle",
        description="Lifecycle edge gate validation",
        domain=ProjectDomain.PV,
        scale=ProjectScale.UTILITY,
        status=ProjectStatus.DRAFT,
        owner_id=owner_id,
    )
    project.id = uuid.uuid4()
    session.add(project)
    session.flush()
    return project


def _first_role_or_default(roles: list[str], default: str) -> str:
    return roles[0] if roles else default


def test_edge_gate_G0_entry_approve_ok(client: TestClient, project_id: str, set_roles) -> None:
    set_roles(["project_manager", "engineer"])

    response = client.get(f"/projects/{project_id}/lifecycle")
    assert response.status_code == 200
    phases = response.json()
    p0 = next(phase for phase in phases if phase["phase_code"] == 0)
    role_key = _first_role_or_default(p0.get("required_entry_roles", []), "role.project_manager")

    payload = {
        "phase_code": 0,
        "gate_code": p0["entry_gate_code"],
        "decision": "APPROVE",
        "role_key": role_key,
        "comment": "edge approve",
    }

    submit = client.post(
        f"/projects/{project_id}/lifecycle/approvals",
        json=payload,
    )
    assert submit.status_code == 200

    updated = submit.json()
    p0_updated = next(phase for phase in updated if phase["phase_code"] == 0)
    entry_gate = next(g for g in p0_updated["gates"] if g["gate_code"] == p0_updated["entry_gate_code"])
    assert entry_gate["status"] == GateStatus.APPROVED.value


def test_edge_gate_G10_exit_reject_ok(client: TestClient, project_id: str, set_roles) -> None:
    set_roles(["project_manager", "approver"])

    res = client.get(f"/projects/{project_id}/lifecycle")
    assert res.status_code == 200
    phases = res.json()
    p10 = next(phase for phase in phases if phase["phase_code"] == 10)
    role_key = _first_role_or_default(p10.get("required_exit_roles", []), "role.project_manager")

    payload = {
        "phase_code": 10,
        "gate_code": p10["exit_gate_code"],
        "decision": "REJECT",
        "role_key": role_key,
    }

    submit = client.post(
        f"/projects/{project_id}/lifecycle/approvals",
        json=payload,
    )
    assert submit.status_code == 200

    updated = submit.json()
    p10_updated = next(phase for phase in updated if phase["phase_code"] == 10)
    exit_gate = next(g for g in p10_updated["gates"] if g["gate_code"] == p10_updated["exit_gate_code"])
    assert exit_gate["status"] == GateStatus.REJECTED.value


def test_edge_gate_RBAC_forbidden_entry(client: TestClient, project_id: str, set_roles) -> None:
    set_roles(["viewer"])

    res = client.get(f"/projects/{project_id}/lifecycle")
    assert res.status_code == 200
    p0 = next(phase for phase in res.json() if phase["phase_code"] == 0)

    payload = {
        "phase_code": 0,
        "gate_code": p0["entry_gate_code"],
        "decision": "APPROVE",
        "role_key": "role.unauthorized",
    }

    submit = client.post(
        f"/projects/{project_id}/lifecycle/approvals",
        json=payload,
    )
    assert submit.status_code == 403


def test_edge_gate_G9_handover_approve_then_idempotent(client: TestClient, session: Session, project_id: str, set_roles) -> None:
    set_roles(["project_manager", "approver"])

    res = client.get(f"/projects/{project_id}/lifecycle")
    assert res.status_code == 200
    phases = res.json()
    p9 = next(phase for phase in phases if phase["phase_code"] == 9)
    role_candidates = (
        p9.get("required_exit_roles")
        or p9.get("required_entry_roles")
        or ["role.project_manager"]
    )
    role_key = role_candidates[0]

    payload = {
        "phase_code": 9,
        "gate_code": p9["exit_gate_code"],
        "decision": "APPROVE",
        "role_key": role_key,
    }

    first = client.post(
        f"/projects/{project_id}/lifecycle/approvals",
        json=payload,
    )
    assert first.status_code == 200
    second = client.post(
        f"/projects/{project_id}/lifecycle/approvals",
        json=payload,
    )
    assert second.status_code == 200

    updated = second.json()
    phase_payload = next(phase for phase in updated if phase["phase_code"] == 9)
    exit_gate = next(g for g in phase_payload["gates"] if g["gate_code"] == phase_payload["exit_gate_code"])
    assert exit_gate["status"] == GateStatus.APPROVED.value

    gate_rows = session.execute(
        select(LifecycleGate).where(
            LifecycleGate.project_id == uuid.UUID(project_id),
            LifecycleGate.phase_code == 9,
            LifecycleGate.gate_code == payload["gate_code"],
        )
    ).scalars().all()
    assert len(gate_rows) == 1
