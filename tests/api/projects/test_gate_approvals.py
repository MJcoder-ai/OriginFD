import os
import sys
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

PACKAGES_ROOT = os.path.join(PROJECT_ROOT, "packages", "py")
if PACKAGES_ROOT not in sys.path:
    sys.path.insert(0, PACKAGES_ROOT)

from api.routers import projects  # noqa: E402
from core.database import SessionDep  # noqa: E402
import models  # noqa: E402
from models.project import (  # noqa: E402
    ProjectDomain,
    ProjectScale,
    ProjectStatus,
)


class FakeSession:
    """In-memory session to validate gate approval behaviour."""

    def __init__(self, project: models.Project, document: models.Document):
        self._projects = {project.id: project}
        self.documents = [document]
        self.committed = False
        self.rolled_back = False

    def get(self, model, ident):  # pragma: no cover - exercised in tests
        if model is models.Project:
            key = ident if isinstance(ident, uuid.UUID) else uuid.UUID(str(ident))
            return self._projects.get(key)
        if model is models.Document:
            key = ident if isinstance(ident, uuid.UUID) else uuid.UUID(str(ident))
            for document in self.documents:
                if document.id == key:
                    return document
        return None

    def commit(self):
        self.committed = True

    def rollback(self):  # pragma: no cover - defensive
        self.rolled_back = True

    def refresh(self, obj):  # pragma: no cover - compatibility no-op
        return obj


class StubProject:
    def __init__(self, user_id: uuid.UUID):
        now = datetime.now(timezone.utc)
        self.id = uuid.uuid4()
        self.name = "Gate Approval Project"
        self.description = "Lifecycle approval checks"
        self.domain = ProjectDomain.PV
        self.scale = ProjectScale.UTILITY
        self.status = ProjectStatus.DRAFT
        self.owner_id = user_id
        self.display_status = "draft"
        self.completion_percentage = 0
        self.created_at = now
        self.updated_at = now
        self.primary_document_id = None

    def can_edit(self, user_id: str) -> bool:  # pragma: no cover - simple stub
        return True


class StubDocument:
    def __init__(self, project: StubProject):
        now = datetime.now(timezone.utc)
        self.id = uuid.uuid4()
        self.tenant_id = uuid.uuid4()
        self.project_name = project.name
        self.domain = project.domain.value
        self.scale = project.scale.value
        self.current_version = 1
        self.content_hash = "sha256:" + "0" * 64
        self.document_data = {
            "meta": {
                "versioning": {
                    "document_version": "4.1.0",
                    "content_hash": self.content_hash,
                }
            },
            "audit": [],
        }
        self.created_at = now
        self.updated_at = now


def _build_project_and_document(user_id: uuid.UUID):
    project = StubProject(user_id)
    document = StubDocument(project)
    project.primary_document_id = document.id
    return project, document


@pytest.fixture()
def make_client():
    def _make(roles: list[str]):
        projects.PROJECT_LIFECYCLE_STATE.clear()

        user_id = uuid.uuid4()
        project, document = _build_project_and_document(user_id)

        app = FastAPI()
        app.include_router(projects.router, prefix="/projects")

        fake_session = FakeSession(project, document)
        app.dependency_overrides[SessionDep] = lambda: fake_session

        tenant_id = uuid.uuid4()
        current_user = {
            "id": str(user_id),
            "email": "approver@example.com",
            "tenant_id": str(tenant_id),
            "roles": roles,
        }
        app.dependency_overrides[projects.get_current_user] = lambda: current_user

        client = TestClient(app)

        projects._ensure_lifecycle(str(project.id))

        return SimpleNamespace(
            client=client,
            session=fake_session,
            project=project,
            document=document,
            user_id=user_id,
        )

    return _make


def _find_gate(project_id: str, gate_id: str):
    lifecycle = projects.PROJECT_LIFECYCLE_STATE.get(project_id, {})
    for phase in lifecycle.get("phases", []):
        for gate in phase.get("gates", []):
            if gate.get("id") == gate_id:
                return gate
    raise AssertionError(f"Gate {gate_id} not found for project {project_id}")


def test_gate_approval_records_audit_and_progress(make_client):
    setup = make_client(["approver"])
    gate_id = "site_assessment"
    project_id = str(setup.project.id)

    response = setup.client.post(
        f"/projects/{project_id}/lifecycle/gates/{gate_id}/status",
        json={"status": "approved", "notes": "Ready to proceed"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved"
    assert payload["phase_id"] == "design"
    assert payload["approved_by"] == str(setup.user_id)
    assert payload["notes"] == "Ready to proceed"
    approved_at = payload["approved_at"]
    updated_at = payload["updated_at"]
    assert approved_at is not None
    assert updated_at is not None
    datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

    gate_state = _find_gate(project_id, gate_id)
    assert gate_state["status"] == "approved"
    assert gate_state["approved_by"] == str(setup.user_id)
    assert gate_state["notes"] == "Ready to proceed"

    assert setup.project.display_status == "in_gate_review"
    assert setup.project.completion_percentage == 20

    audit_log = setup.document.document_data.get("audit", [])
    assert audit_log, "Expected audit entry to be created"
    assert audit_log[-1]["actor"] == str(setup.user_id)
    assert audit_log[-1]["details"]["patch_operations"] == 1

    assert setup.session.committed is True


def test_gate_approval_requires_authorized_role(make_client):
    setup = make_client(["viewer"])
    project_id = str(setup.project.id)

    response = setup.client.post(
        f"/projects/{project_id}/lifecycle/gates/site_assessment/status",
        json={"status": "approved"},
    )

    assert response.status_code == 403

    gate_state = _find_gate(project_id, "site_assessment")
    assert gate_state["status"] == "pending"
    assert setup.project.display_status == "draft"
    assert setup.project.completion_percentage == 0
    assert setup.document.document_data.get("audit", []) == []
    assert setup.session.committed is False
