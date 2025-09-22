"""Regression tests for the component integration router."""

import copy
import os
import sys
import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

PACKAGES_ROOT = os.path.join(PROJECT_ROOT, "packages", "py")
if PACKAGES_ROOT not in sys.path:
    sys.path.insert(0, PACKAGES_ROOT)


from api.routers import component_integration  # noqa: E402
from deps import get_current_user  # noqa: E402
from core.database import SessionDep  # noqa: E402
import models  # noqa: E402
from models.document import DocumentVersion  # noqa: E402


if not hasattr(models, "DocumentVersion"):
    setattr(models, "DocumentVersion", DocumentVersion)


class FakeQuery:
    """Minimal query object supporting the interface used by the router."""

    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):  # pragma: no cover - parameters unused
        return self

    def order_by(self, *args, **kwargs):  # pragma: no cover - ordering not needed
        return self

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result


class FakeSession:
    """In-memory session storing added objects for assertions."""

    def __init__(self, document, current_version, component):
        self.document = document
        self.current_version = current_version
        self.component = component
        self.added_objects = []
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        if model is models.Component:
            return FakeQuery(self.component)
        if model is models.Document:
            return FakeQuery(self.document)
        if model is models.DocumentVersion:
            return FakeQuery([self.current_version])
        return FakeQuery(None)

    def add(self, obj):
        self.added_objects.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class StubOdlDocument:
    """Simple stub mirroring the OdlDocument interface used in the router."""

    def __init__(self, data):
        self._data = copy.deepcopy(data)

    @classmethod
    def model_validate(cls, data):
        return cls(data)

    def model_dump(self):
        return copy.deepcopy(self._data)


@pytest.fixture()
def component_binding_client(monkeypatch):
    """Create a test client with stubbed dependencies for component binding."""

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    document_id = uuid.uuid4()
    component_db_id = uuid.uuid4()

    base_document = {
        "meta": {
            "project": "Demo Project",
            "versioning": {
                "document_version": "1.0.0",
                "content_hash": "sha256:original",
            },
        },
        "libraries": {"components": []},
    }

    existing_version = DocumentVersion(
        tenant_id=tenant_id,
        document_id=document_id,
        version_number=1,
        content_hash=base_document["meta"]["versioning"]["content_hash"],
        previous_hash=None,
        change_summary="Initial",
        patch_operations=None,
        evidence_uris=None,
        created_by=user_id,
        document_data=copy.deepcopy(base_document),
    )

    document = SimpleNamespace(
        id=document_id,
        tenant_id=tenant_id,
        project_name="Demo Project",
        current_version=1,
        content_hash=existing_version.content_hash,
        document_data=copy.deepcopy(base_document),
        updated_at=datetime.utcnow(),
    )

    class StubManagement:
        def __init__(self):
            self.media = {"doc_bindings": {"bindings": []}}
            self.version = "1.0"
            self.tracking_policy = {}
            self.traceability = {}
            self.audit_records = []

        def add_audit_record(self, **kwargs):
            self.audit_records.append(kwargs)

    component = SimpleNamespace(
        id=component_db_id,
        tenant_id=tenant_id,
        component_id="CMP-001",
        name="Inverter",
        brand="OriginFD",
        part_number="INV-1000",
        rating_w=1000,
        category="Power",
        subcategory="Inverter",
        domain="PV",
        scale="UTILITY",
        status="active",
        classification="electrical",
        is_active=True,
        management=StubManagement(),
    )

    expected_document = copy.deepcopy(base_document)
    expected_document["libraries"]["components"].append(
        {
            "component_id": component.component_id,
            "name": component.name,
            "binding_type": "library",
        }
    )

    def fake_apply_patch(document_data, patch_ops, **kwargs):
        return copy.deepcopy(expected_document)

    expected_patch_ops = [
        {
            "op": "add",
            "path": "/libraries/components/0",
            "value": {"component_id": component.component_id},
        }
    ]

    fake_session = FakeSession(document, existing_version, component)

    app = FastAPI()
    app.include_router(component_integration.router, prefix="/component-integration")

    monkeypatch.setattr(component_integration, "OdlDocument", StubOdlDocument)
    monkeypatch.setattr(component_integration, "apply_patch", fake_apply_patch)
    monkeypatch.setattr(
        component_integration,
        "create_component_binding_patch",
        lambda *args, **kwargs: expected_patch_ops,
    )
    monkeypatch.setattr(models.Component, "tenant_id", object(), raising=False)

    app.dependency_overrides[SessionDep] = lambda: fake_session
    app.dependency_overrides[get_current_user] = lambda: {
        "id": str(user_id),
        "tenant_id": str(tenant_id),
        "email": "engineer@example.com",
    }

    client = TestClient(app)
    client.fake_session = fake_session  # type: ignore[attr-defined]
    client.document = document  # type: ignore[attr-defined]
    client.component = component  # type: ignore[attr-defined]
    client.expected_document = expected_document  # type: ignore[attr-defined]
    client.user_id = user_id  # type: ignore[attr-defined]
    client.current_version = existing_version  # type: ignore[attr-defined]
    client.expected_patch_ops = expected_patch_ops  # type: ignore[attr-defined]
    return client


def test_bind_component_persists_document_version(component_binding_client):
    """Binding a component should create a new DocumentVersion with document data."""

    client = component_binding_client
    document = client.document
    fake_session = client.fake_session
    expected_document = client.expected_document
    previous_version = client.current_version

    payload = {
        "component_id": str(client.component.id),
        "document_id": str(document.id),
        "binding_type": "library",
        "location_path": "libraries.components",
    }

    response = client.post("/component-integration/bind", json=payload)

    assert response.status_code == 201

    version_record = next(
        obj for obj in fake_session.added_objects if isinstance(obj, models.DocumentVersion)
    )

    expected_state = copy.deepcopy(expected_document)
    versioning_meta = expected_state.setdefault("meta", {}).setdefault("versioning", {})
    versioning_meta["previous_hash"] = previous_version.content_hash
    expected_hash = component_integration.calculate_content_hash(expected_state)
    versioning_meta["content_hash"] = expected_hash

    assert version_record.tenant_id == document.tenant_id
    assert version_record.document_id == document.id
    assert version_record.version_number == previous_version.version_number + 1
    assert version_record.previous_hash == previous_version.content_hash
    assert version_record.content_hash == expected_hash
    assert version_record.document_data == expected_state
    assert version_record.patch_operations == client.expected_patch_ops
    assert version_record.created_by == client.user_id
    assert "Inverter" in version_record.change_summary

    # Document should be updated to reflect the latest version
    assert document.current_version == version_record.version_number
    assert document.content_hash == expected_hash
    assert document.document_data == expected_state

    # The component binding should be reflected in the stored document
    components = document.document_data["libraries"]["components"]
    assert any(item["component_id"] == client.component.component_id for item in components)

    # Ensure the session completed successfully
    assert fake_session.committed is True
    assert fake_session.rolled_back is False
