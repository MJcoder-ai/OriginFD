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
from models.document import DocumentVersion as SADocumentVersion  # noqa: E402


if not hasattr(models, "DocumentVersion"):
    setattr(models, "DocumentVersion", SADocumentVersion)


class FakeQuery:
    """Minimal query object used to satisfy the router's query calls."""

    def __init__(self, result=None):
        self._result = result or []

    def filter(self, *args, **kwargs):  # pragma: no cover - unused chain support
        return self

    def order_by(self, *args, **kwargs):  # pragma: no cover - unused chain support
        return self

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result


class FakeSession:
    """In-memory session capturing objects for assertions."""

    def __init__(self):
        self.projects = []
        self.documents = []
        self.document_versions = []
        self._pending = []
        self.committed = False
        self.rolled_back = False

    def query(self, model):  # pragma: no cover - not used in tests yet
        return FakeQuery([])

    def add(self, obj):
        self._pending.append(obj)
        if isinstance(obj, models.Project):
            self.projects.append(obj)
        elif isinstance(obj, models.Document):
            self.documents.append(obj)
        elif isinstance(obj, SADocumentVersion):
            self.document_versions.append(obj)

    def flush(self):
        now = datetime.now(timezone.utc)
        for obj in list(self._pending):
            if isinstance(obj, models.Project) and getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
                obj.created_at = getattr(obj, "created_at", None) or now
                obj.updated_at = getattr(obj, "updated_at", None) or now
                if getattr(obj, "display_status", None) is None:
                    obj.display_status = "draft"
                if getattr(obj, "completion_percentage", None) is None:
                    obj.completion_percentage = 0
            elif isinstance(obj, models.Document) and getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
                obj.created_at = getattr(obj, "created_at", None) or now
                obj.updated_at = getattr(obj, "updated_at", None) or now
            elif isinstance(obj, SADocumentVersion) and getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
                obj.created_at = getattr(obj, "created_at", None) or now
        self._pending.clear()

    def commit(self):
        self.committed = True

    def rollback(self):  # pragma: no cover - defensive
        self.rolled_back = True

    def refresh(self, obj):  # pragma: no cover - compatibility no-op
        return obj


class StubDocument:
    """Simple document stub mimicking the generator output."""

    def __init__(self, content_hash: str):
        self.meta = SimpleNamespace(
            versioning=SimpleNamespace(content_hash=content_hash)
        )
        self._payload = {
            "meta": {"versioning": {"content_hash": content_hash}},
            "data": {"placeholder": True},
        }

    def validate_document(self):
        return True, []

    def to_dict(self):
        return self._payload


class StubDocumentGenerator:
    @staticmethod
    def create_project_document(*args, **kwargs):
        return StubDocument(f"sha256:{uuid.uuid4().hex}")


@pytest.fixture()
def test_client(monkeypatch):
    app = FastAPI()
    app.include_router(projects.router, prefix="/projects")

    fake_session = FakeSession()
    app.dependency_overrides[SessionDep] = lambda: fake_session

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    app.dependency_overrides[projects.get_current_user] = lambda: {
        "id": str(user_id),
        "email": "user@example.com",
        "tenant_id": str(tenant_id),
    }

    monkeypatch.setattr(projects, "DocumentGenerator", StubDocumentGenerator)

    client = TestClient(app)
    client.fake_session = fake_session  # type: ignore[attr-defined]
    client.tenant_id = tenant_id  # type: ignore[attr-defined]
    client.user_id = user_id  # type: ignore[attr-defined]
    return client


def _project_payload():
    return {
        "name": "Tenant Scoped Project",
        "description": "Project tied to a tenant",
        "domain": "PV",
        "scale": "utility",
        "location_name": "Berlin",
        "total_capacity_kw": 42.5,
        "tags": ["demo"],
    }


def test_create_project_links_primary_document(test_client):
    response = test_client.post("/projects/", json=_project_payload())

    assert response.status_code == 200
    data = response.json()

    fake_session: FakeSession = test_client.fake_session  # type: ignore[assignment]
    assert fake_session.committed is True
    assert fake_session.projects, "Project was not persisted"
    assert fake_session.documents, "Document was not persisted"

    project = fake_session.projects[0]
    document = fake_session.documents[0]

    assert project.primary_document_id == document.id

    assert data["primary_document_id"] == str(document.id)
    assert data["document"]["id"] == str(document.id)
    assert data["document"]["content_hash"] == document.content_hash
    assert data["document"]["version"] == document.current_version
    assert data["document_id"] == str(document.id)
    assert data["document_hash"] == document.content_hash


def test_create_project_requires_tenant_context(test_client):
    original_dependency = test_client.app.dependency_overrides[  # type: ignore[attr-defined]
        projects.get_current_user
    ]
    test_client.app.dependency_overrides[projects.get_current_user] = lambda: {  # type: ignore[attr-defined]
        "id": str(uuid.uuid4())
    }

    try:
        response = test_client.post("/projects/", json=_project_payload())
    finally:
        test_client.app.dependency_overrides[projects.get_current_user] = (  # type: ignore[attr-defined]
            original_dependency
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Tenant context is required to create a project"
    assert test_client.fake_session.committed is False  # type: ignore[attr-defined]
