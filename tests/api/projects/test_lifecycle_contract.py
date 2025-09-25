import importlib
import sys
from pathlib import Path
from typing import Dict, Iterable, List
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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

from core.database import get_db
from services.api.api.routers.auth import get_current_user
from services.api.main import app
from services.api.models import LifecycleGate, LifecyclePhase
from services.api.models.document import Document
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

EXPECTED_PHASE_KEYS = {
    "phase_code",
    "phase_key",
    "title",
    "order",
    "entry_gate_code",
    "exit_gate_code",
    "required_entry_roles",
    "required_exit_roles",
    "odl_sd_sections",
    "name",
    "status",
    "gates",
}
EXPECTED_GATE_KEYS = {"key", "name", "gate_code", "status"}
EXPECTED_STATUSES = {status.value for status in GateStatus}


def _create_user(session: Session) -> User:
    user = User(
        email="contract-snapshot@originfd.com",
        hashed_password="test-hash",
        full_name="Lifecycle Contract",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="engineer",
    )
    user.id = uuid.uuid4()
    session.add(user)
    session.flush()
    return user


def _create_project(session: Session, owner_id) -> Project:
    project = Project(
        name="Lifecycle Contract Snapshot",
        description="",
        domain=ProjectDomain.PV,
        scale=ProjectScale.UTILITY,
        status=ProjectStatus.DRAFT,
        owner_id=owner_id,
    )
    project.id = uuid.uuid4()
    session.add(project)
    session.flush()
    return project


@pytest.fixture()
def lifecycle_contract_env():
    engine = make_sqlite_engine()
    tables = [
        Document.__table__,
        User.__table__,
        Project.__table__,
        LifecyclePhase.__table__,
        LifecycleGate.__table__,
    ]
    create_tables(engine, tables)
    SessionLocal = session_factory(engine)

    with SessionLocal() as seed_session:
        user = _create_user(seed_session)
        project = _create_project(seed_session, user.id)
        seed_lifecycle_catalog(seed_session, project=project)
        seed_session.commit()
        project_id = project.id
        user_id = user.id

    current_user_state: Dict[str, object] = {
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

    def override_current_user() -> Dict[str, object]:
        return current_user_state

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    client = TestClient(app)

    try:
        yield client, str(project_id)
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        drop_tables(engine, tables)
        engine.dispose()


@pytest.fixture()
def snapshot_client(lifecycle_contract_env):
    client, _ = lifecycle_contract_env
    return client


@pytest.fixture()
def snapshot_project_id(lifecycle_contract_env):
    _, project_id = lifecycle_contract_env
    return project_id


def test_get_lifecycle_contract_shape(snapshot_client: TestClient, snapshot_project_id: str) -> None:
    response = snapshot_client.get(f"/projects/{snapshot_project_id}/lifecycle")
    assert response.status_code == 200

    payload: List[Dict[str, object]] = response.json()
    assert len(payload) == 12

    previous_order = -1
    for phase in payload:
        assert EXPECTED_PHASE_KEYS.issubset(phase.keys())
        assert isinstance(phase["gates"], list)
        assert len(phase["gates"]) == 2

        for gate in phase["gates"]:
            assert EXPECTED_GATE_KEYS.issubset(gate.keys())
            assert gate["status"] in EXPECTED_STATUSES

        assert phase["order"] > previous_order
        previous_order = phase["order"]

    assert previous_order >= 11
