
import uuid
from typing import Dict, List

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT / "services"))
sys.path.append(str(ROOT / "services" / "api"))
import importlib

models_module = importlib.import_module("services.api.models")
sys.modules.setdefault("models", models_module)
sys.modules.setdefault("core", importlib.import_module("services.api.core"))

for name, module in list(sys.modules.items()):
    if name.startswith("services.api.models"):
        alias = name.replace("services.api.models", "models", 1)
        sys.modules.setdefault(alias, module)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.api.main import app
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
from services.api.models.lifecycle import GateStatus
from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog
from services.api.domain.lifecycle_catalog import LIFECYCLE_CATALOG
from core.database import get_db
from services.api.api.routers.auth import get_current_user

from tests.api._utils.sqlite_harness import (
    create_tables,
    drop_tables,
    make_sqlite_engine,
    session_factory,
)


@pytest.fixture()
def lifecycle_client() -> TestClient:
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

    with SessionLocal() as session:
        user = _create_user(session)
        project = _create_project(session, user.id)
        seed_lifecycle_catalog(session, project=project)
        session.commit()
        user_id = user.id
        project_id = project.id

    def override_get_db():
        db: Session = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_current_user() -> Dict[str, str]:
        return {
            "id": str(user_id),
            "roles": [
                "project_manager",
                "engineer",
                "approver",
            ],
            "tenant_id": str(uuid.uuid4()),
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    client = TestClient(app)
    try:
        yield client, str(project_id)
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        drop_tables(engine, tables)
        engine.dispose()


def _create_user(session: Session) -> User:
    user = User(
        email="lifecycle-smoke@originfd.com",
        hashed_password="test-hash",
        full_name="Lifecycle Smoke",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="engineer",
    )
    session.add(user)
    session.flush()
    return user


def _create_project(session: Session, owner_id) -> Project:
    project = Project(
        name="Lifecycle Smoke Project",
        description="",
        domain=ProjectDomain.PV,
        scale=ProjectScale.UTILITY,
        status=ProjectStatus.DRAFT,
        owner_id=owner_id,
    )
    session.add(project)
    session.flush()
    return project


def test_get_lifecycle_returns_12_phases(lifecycle_client) -> None:
    client, project_id = lifecycle_client

    response = client.get(f"/projects/{project_id}/lifecycle")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == len(LIFECYCLE_CATALOG)

    phase_codes = [item["phase_code"] for item in payload]
    assert phase_codes == list(range(len(LIFECYCLE_CATALOG)))

    for phase in payload:
        gates: List[Dict[str, str]] = phase.get("gates", [])
        assert len(gates) == 2
        for gate in gates:
            assert gate["status"] == GateStatus.NOT_STARTED.value


def test_post_gate_approval_persists_and_reflects_in_get(lifecycle_client) -> None:
    client, project_id = lifecycle_client

    phase_spec = LIFECYCLE_CATALOG[0]
    entry_gate_code = phase_spec.entry_gate_code
    role_key = phase_spec.required_entry_roles[0]

    payload = {
        "phase_code": phase_spec.phase_code,
        "gate_code": entry_gate_code,
        "decision": "APPROVE",
        "role_key": role_key,
        "comment": "smoke ok",
    }

    response = client.post(
        f"/projects/{project_id}/lifecycle/gates/{entry_gate_code}/status",
        json=payload,
    )
    assert response.status_code == 200

    updated = response.json()
    phase = next(item for item in updated if item["phase_code"] == phase_spec.phase_code)
    entry_gate = next(g for g in phase["gates"] if g["gate_code"] == entry_gate_code)
    assert entry_gate["status"] == GateStatus.APPROVED.value

    follow_up = client.get(f"/projects/{project_id}/lifecycle")
    assert follow_up.status_code == 200
    phase_after = next(item for item in follow_up.json() if item["phase_code"] == phase_spec.phase_code)
    entry_gate_after = next(
        g for g in phase_after["gates"] if g["gate_code"] == entry_gate_code
    )
    assert entry_gate_after["status"] == GateStatus.APPROVED.value
