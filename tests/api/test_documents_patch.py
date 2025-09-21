import os
import sys
import uuid
from datetime import datetime
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure the API package and models are importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

PACKAGES_ROOT = os.path.join(PROJECT_ROOT, "packages", "py")
if PACKAGES_ROOT not in sys.path:
    sys.path.insert(0, PACKAGES_ROOT)

from api.routers import documents  # noqa: E402
from core.database import SessionDep  # noqa: E402
from core.auth import get_current_user  # noqa: E402
import models  # noqa: E402
from models.document import DocumentVersion  # noqa: E402

# Ensure DocumentVersion is accessible via the models package
if not hasattr(models, "DocumentVersion"):
    setattr(models, "DocumentVersion", DocumentVersion)


class FakeQuery:
    """Minimal query object that mimics SQLAlchemy's chaining interface."""

    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def order_by(self, *args, **kwargs):  # pragma: no cover - compatibility
        return self

    def offset(self, *args, **kwargs):  # pragma: no cover - compatibility
        return self

    def limit(self, *args, **kwargs):  # pragma: no cover - compatibility
        return self

    def first(self):
        return self._result

    def all(self):  # pragma: no cover - compatibility
        return self._result if isinstance(self._result, list) else []


class FakeSession:
    """In-memory session that mimics the SQLAlchemy interface used by the router."""

    def __init__(self, document):
        self.document = document
        self.added_objects = []
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        if model is models.Document:
            return FakeQuery(self.document)
        if model is models.DocumentVersion:
            return FakeQuery([])
        return FakeQuery(None)

    def add(self, obj):
        self.added_objects.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):  # pragma: no cover - compatibility
        return obj


@pytest.fixture()
def sample_document():
    """Create a minimal valid ODL-SD document payload."""

    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "$schema": "https://odl-sd.org/schemas/v4.1/document.json",
        "schema_version": "4.1",
        "meta": {
            "project": "Demo Project",
            "domain": "PV",
            "scale": "UTILITY",
            "units": {
                "system": "SI",
                "currency": "USD",
                "coordinate_system": "EPSG:4326",
            },
            "timestamps": {"created_at": timestamp, "updated_at": timestamp},
            "versioning": {
                "document_version": "1.0.0",
                "content_hash": "sha256:original",
            },
        },
        "hierarchy": {"sites": [{"id": "site-1"}]},
        "requirements": {},
        "libraries": {},
        "instances": [
            {
                "id": "component-1",
                "type": "inverter",
                "parameters": {"capacity_kw": 100},
                "metadata": {},
            }
        ],
        "connections": [],
        "analysis": [],
        "audit": [],
        "data_management": {
            "partitioning_enabled": False,
            "external_refs_enabled": False,
            "streaming_enabled": False,
            "max_document_size_mb": 100,
        },
    }


@pytest.fixture()
def test_client(sample_document, monkeypatch):
    """Create a FastAPI TestClient with overridden dependencies."""

    app = FastAPI()
    app.include_router(documents.router, prefix="/documents")

    class StubOdlDocument:
        def __init__(self, data):
            self._data = data
            self.meta = SimpleNamespace(
                versioning=SimpleNamespace(
                    content_hash=data["meta"]["versioning"]["content_hash"]
                )
            )

        @classmethod
        def parse_obj(cls, data):
            return cls(data)

        def validate_document(self):
            return SimpleNamespace(is_valid=True, errors=[])

    monkeypatch.setattr(documents, "OdlSdDocument", StubOdlDocument)

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    document = models.Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        project_name=sample_document["meta"]["project"],
        portfolio_id=None,
        domain=sample_document["meta"]["domain"],
        scale=sample_document["meta"]["scale"],
        current_version=1,
        content_hash=sample_document["meta"]["versioning"]["content_hash"],
        document_data=sample_document,
    )
    document.created_at = datetime.utcnow()
    document.updated_at = datetime.utcnow()
    document.is_active = True

    fake_session = FakeSession(document)

    app.dependency_overrides[SessionDep] = lambda: fake_session
    app.dependency_overrides[get_current_user] = lambda: {
        "id": str(user_id),
        "tenant_id": str(tenant_id),
    }

    client = TestClient(app)
    client.fake_session = fake_session  # type: ignore[attr-defined]
    client.document = document  # type: ignore[attr-defined]
    return client


def test_patch_document_success(test_client):
    """Applying a JSON-Patch request updates the document and returns success."""

    document = test_client.document
    fake_session = test_client.fake_session

    payload = {
        "doc_id": str(document.id),
        "doc_version": document.current_version,
        "patch": [
            {"op": "replace", "path": "/meta/project", "value": "Updated Project"}
        ],
        "evidence": ["s3://bucket/change.pdf"],
        "dry_run": False,
        "change_summary": "Rename project",
    }

    response = test_client.post("/documents/patch", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["doc_version"] == 2
    assert body["inverse_patch"], "Expected inverse patch operations to be returned"

    # Document state should be updated in-place
    assert document.current_version == 2
    assert document.document_data["meta"]["project"] == "Updated Project"
    assert document.document_data["audit"], "Audit trail should record the patch"

    # Database session interactions should commit without rollback
    assert fake_session.committed is True
    assert fake_session.rolled_back is False
    assert fake_session.added_objects, "DocumentVersion should be recorded"
