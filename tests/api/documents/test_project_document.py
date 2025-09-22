"""Tests for retrieving a project's active document."""

from __future__ import annotations

import os
import sys
import uuid
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

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

from api.routers import documents  # noqa: E402
from core.database import SessionDep  # noqa: E402
from core.permissions import (  # noqa: E402
    AuthorizationContext,
    Permission,
    ResourceType,
    get_permission_checker,
    get_project_for_user,
)
from deps import get_current_user  # noqa: E402
import models  # noqa: E402


class FakeQuery:
    """Mimic a SQLAlchemy query chain used by the endpoint."""

    def __init__(self, result: Optional[Any]):
        self.result = result
        self.joins: List[Any] = []
        self.filters: List[Any] = []

    def join(self, *args: Any, **kwargs: Any) -> "FakeQuery":
        self.joins.append((args, kwargs))
        return self

    def filter(self, *criteria: Any) -> "FakeQuery":
        self.filters.extend(criteria)
        return self

    def first(self) -> Optional[Any]:
        return self.result


class FakeSession:
    """Minimal session returning a prepared query result."""

    def __init__(self, document: Optional[Any]):
        self.document = document
        self.queries: List[Any] = []

    def query(self, model: Any) -> FakeQuery:
        assert model is models.Document, "Query should target the Document model"
        self.queries.append(model)
        return FakeQuery(self.document)


class StubPermissionChecker:
    """Capture authorization checks performed by the endpoint."""

    def __init__(self) -> None:
        self.contexts: List[AuthorizationContext] = []

    def authorize(self, context: AuthorizationContext) -> bool:
        self.contexts.append(context)
        return True


@pytest.fixture
def user_payload() -> Dict[str, str]:
    return {"id": str(uuid.uuid4()), "tenant_id": str(uuid.uuid4())}


def create_test_client(
    project: Any,
    document: Optional[Any],
    user_payload: Dict[str, str],
):
    app = FastAPI()
    app.include_router(documents.project_router, prefix="/projects")

    fake_session = FakeSession(document)
    permission_checker = StubPermissionChecker()

    def override_get_current_user() -> Dict[str, str]:
        return user_payload

    def override_get_project_for_user(
        project_id: uuid.UUID,
        user: Dict[str, Any] | None = None,
        checker: Any | None = None,
    ) -> Any:
        assert project_id == project.id
        return project

    def override_get_permission_checker() -> StubPermissionChecker:
        return permission_checker

    app.dependency_overrides[SessionDep] = lambda: fake_session
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_project_for_user] = override_get_project_for_user
    app.dependency_overrides[get_permission_checker] = override_get_permission_checker

    client = TestClient(app)
    client.fake_session = fake_session  # type: ignore[attr-defined]
    client.permission_checker = permission_checker  # type: ignore[attr-defined]
    return client


def test_get_project_document_success(user_payload: Dict[str, str]):
    project_id = uuid.uuid4()
    document_id = uuid.uuid4()
    project = SimpleNamespace(id=project_id, primary_document_id=document_id)
    document = SimpleNamespace(
        id=document_id,
        document_data={"meta": {"project": "Alpha"}},
        tenant_id=uuid.UUID(user_payload["tenant_id"]),
        is_active=True,
    )

    client = create_test_client(project, document, user_payload)

    response = client.get(f"/projects/{project_id}/document")

    assert response.status_code == 200
    assert response.json() == {"meta": {"project": "Alpha"}}

    contexts = client.permission_checker.contexts  # type: ignore[attr-defined]
    assert contexts, "Authorization should be invoked"
    context = contexts[0]
    assert context.action == Permission.DOCUMENT_READ
    assert context.resource_type == ResourceType.DOCUMENT
    assert context.resource_id == document_id


def test_get_project_document_missing_primary(user_payload: Dict[str, str]):
    project_id = uuid.uuid4()
    project = SimpleNamespace(id=project_id, primary_document_id=None)

    client = create_test_client(project, None, user_payload)

    response = client.get(f"/projects/{project_id}/document")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project does not have an active document"


def test_get_project_document_not_found(user_payload: Dict[str, str]):
    project_id = uuid.uuid4()
    document_id = uuid.uuid4()
    project = SimpleNamespace(id=project_id, primary_document_id=document_id)

    client = create_test_client(project, None, user_payload)

    response = client.get(f"/projects/{project_id}/document")

    assert response.status_code == 404
    assert response.json()["detail"] == "Active project document not found"
