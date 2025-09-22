import json
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
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

PACKAGES_ROOT = os.path.join(PROJECT_ROOT, "packages", "py")
if PACKAGES_ROOT not in sys.path:
    sys.path.insert(0, PACKAGES_ROOT)

from api.routers import projects  # noqa: E402
from core.database import SessionDep  # noqa: E402
import models  # noqa: E402
class StubProject:
    """Lightweight stand-in for the SQLAlchemy Project model."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", self.created_at)
        self.display_status = kwargs.get("display_status", "draft")
        self.completion_percentage = kwargs.get("completion_percentage", 0)
        self.primary_document_id = kwargs.get("primary_document_id")
        self.initialization_task_id = kwargs.get("initialization_task_id")
        self.is_archived = kwargs.get("is_archived", False)

        for field, value in kwargs.items():
            setattr(self, field, value)

        self.tags = json.dumps(kwargs.get("tags_list", kwargs.get("tags", [])) or [])

    def can_edit(self, user_id: str) -> bool:
        return str(getattr(self, "owner_id", "")) == user_id

    def can_view(self, user_id: str) -> bool:
        return self.can_edit(user_id)

    @property
    def tags_list(self) -> list[str]:
        try:
            return json.loads(self.tags or "[]")
        except (TypeError, json.JSONDecodeError):
            return []

    @tags_list.setter
    def tags_list(self, value: list[str]) -> None:
        self.tags = json.dumps(value or [])


class StubDocument:
    """Minimal document representation for unit tests."""

    id: uuid.UUID | None = None
    tenant_id: uuid.UUID | None = None

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.tenant_id = kwargs.get("tenant_id")
        self.project_name = kwargs.get("project_name")
        self.portfolio_id = kwargs.get("portfolio_id")
        self.domain = kwargs.get("domain")
        self.scale = kwargs.get("scale")
        self.current_version = kwargs.get("current_version", 1)
        self.content_hash = kwargs.get("content_hash", "")
        self.document_data = kwargs.get("document_data", {})
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", self.created_at)


class StubDocumentVersion:
    """Simple value object capturing document version metadata."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        for field, value in kwargs.items():
            setattr(self, field, value)


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
        elif isinstance(obj, models.DocumentVersion):
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
            elif isinstance(obj, models.DocumentVersion) and getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
                obj.created_at = getattr(obj, "created_at", None) or now
        self._pending.clear()

    def commit(self):
        self.committed = True

    def rollback(self):  # pragma: no cover - defensive
        self.rolled_back = True

    def refresh(self, obj):  # pragma: no cover - compatibility no-op
        return obj


class StubGeneratedDocument:
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
        return StubGeneratedDocument(f"sha256:{uuid.uuid4().hex}")


@pytest.fixture()
def test_client(monkeypatch):
    app = FastAPI()
    app.include_router(projects.router, prefix="/projects")

    monkeypatch.setattr(models, "Project", StubProject)
    monkeypatch.setattr(models, "Document", StubDocument)
    monkeypatch.setattr(models, "DocumentVersion", StubDocumentVersion, raising=False)
    monkeypatch.setattr(projects, "SADocumentVersion", StubDocumentVersion)

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

    publish_calls = []

    def _record_usage(tenant: str, psu: int, metadata: dict | None = None):
        publish_calls.append({
            "tenant_id": tenant,
            "psu": psu,
            "metadata": metadata or {},
        })
        return {"psu": psu, "fee": 0}

    monkeypatch.setattr(projects, "publish_usage_event", _record_usage)

    client = TestClient(app)
    client.fake_session = fake_session  # type: ignore[attr-defined]
    client.tenant_id = tenant_id  # type: ignore[attr-defined]
    client.user_id = user_id  # type: ignore[attr-defined]
    client.publish_calls = publish_calls  # type: ignore[attr-defined]
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

    assert test_client.publish_calls  # type: ignore[attr-defined]
    usage_call = test_client.publish_calls[0]  # type: ignore[index]
    assert usage_call["tenant_id"] == str(test_client.tenant_id)  # type: ignore[attr-defined]
    assert usage_call["psu"] > 0
    assert usage_call["metadata"]["event"] == "project_created"
    assert usage_call["metadata"]["project_id"] == str(project.id)


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
