"""Integration tests for the orchestrator webhook router."""

import copy
import hashlib
import hmac
import json
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

from api.routers import orchestrator  # noqa: E402
from api.services import document_service as document_service_module  # noqa: E402
from core.config import get_settings  # noqa: E402


class FakeQuery:
    """Minimal query object supporting the interface used by the service."""

    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):  # pragma: no cover - arguments unused
        return self

    def with_for_update(self):
        return self

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result


class FakeSession:
    """Simple in-memory session used for orchestrator webhook tests."""

    def __init__(self, document):
        self.document = document
        self.added_objects = []
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        document_model = document_service_module.Document
        version_model = document_service_module.DocumentVersion

        if model is document_model:
            return FakeQuery(self.document)
        if model is version_model:
            return FakeQuery([])
        return FakeQuery(None)

    def add(self, obj):
        self.added_objects.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):  # pragma: no cover - defensive
        self.rolled_back = True


@pytest.fixture()
def sample_document():
    """Create a minimal document payload used in orchestrator tests."""

    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "$schema": "https://odl-sd.org/schemas/v4.1/document.json",
        "schema_version": "4.1",
        "meta": {
            "project": "Demo Project",
            "domain": "PV",
            "scale": "UTILITY",
            "units": {"system": "SI"},
            "timestamps": {"created_at": timestamp, "updated_at": timestamp},
            "versioning": {
                "document_version": "1.0.0",
                "content_hash": "sha256:original",
            },
        },
        "hierarchy": {"sites": [{"id": "site-1", "name": "Baseline"}]},
        "libraries": {},
        "instances": [],
        "connections": [],
        "analysis": [],
        "audit": [],
        "data_management": {},
    }


@pytest.fixture()
def orchestrator_test_context(sample_document, monkeypatch):
    """Set up FastAPI test client with stubbed dependencies."""

    app = FastAPI()
    app.include_router(orchestrator.router, prefix="/orchestrator")

    tenant_id = uuid.uuid4()
    document_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    base_document = copy.deepcopy(sample_document)

    class ColumnStub:
        def __eq__(self, other):  # pragma: no cover - expressions ignored
            return True

        def __hash__(self):  # pragma: no cover - required for comparisons
            return hash("column-stub")

    class StubDocument:
        id = ColumnStub()
        tenant_id = ColumnStub()

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class StubDocumentVersion:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setattr(document_service_module, "Document", StubDocument)
    monkeypatch.setattr(
        document_service_module, "DocumentVersion", StubDocumentVersion
    )

    document = StubDocument(
        id=document_id,
        tenant_id=tenant_id,
        project_name=base_document["meta"]["project"],
        portfolio_id=None,
        domain=base_document["meta"]["domain"],
        scale=base_document["meta"]["scale"],
        current_version=1,
        content_hash=base_document["meta"]["versioning"]["content_hash"],
        document_data=base_document,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True,
    )

    expected_document = copy.deepcopy(base_document)
    expected_document["hierarchy"]["sites"][0]["name"] = "Updated Site"
    expected_document["meta"]["versioning"]["content_hash"] = "sha256:newhash"

    def fake_apply_patch(document_data, patch_ops, **kwargs):
        return copy.deepcopy(expected_document)

    class StubOdlSdDocument:
        def __init__(self, data):
            versioning = data["meta"]["versioning"]
            self.meta = SimpleNamespace(
                versioning=SimpleNamespace(content_hash=versioning["content_hash"])
            )

        @classmethod
        def parse_obj(cls, data):
            return cls(data)

        def validate_document(self):
            return SimpleNamespace(is_valid=True, errors=[])

    monkeypatch.setattr(document_service_module, "apply_patch", fake_apply_patch)
    monkeypatch.setattr(document_service_module, "OdlSdDocument", StubOdlSdDocument)

    fake_session = FakeSession(document)
    document_service = document_service_module.DocumentService(fake_session)

    secret = "whsec_test"

    app.dependency_overrides[orchestrator.get_document_service] = lambda: document_service
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        ORCHESTRATOR_WEBHOOK_SECRET=secret
    )

    client = TestClient(app)

    return {
        "client": client,
        "document": document,
        "session": fake_session,
        "expected_document": expected_document,
        "secret": secret,
        "tenant_id": tenant_id,
        "document_id": document_id,
        "actor_id": actor_id,
    }


def _signed_headers(secret: str, body: str) -> dict[str, str]:
    signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256)
    return {
        "content-type": "application/json",
        orchestrator.SIGNATURE_HEADER: f"sha256={signature.hexdigest()}",
    }


def test_initialization_completed_applies_patch(orchestrator_test_context):
    """The initialization.completed event applies document patches and persists changes."""

    ctx = orchestrator_test_context
    client = ctx["client"]

    payload = {
        "event": "initialization.completed",
        "data": {
            "document_id": str(ctx["document_id"]),
            "tenant_id": str(ctx["tenant_id"]),
            "document_version": ctx["document"].current_version,
            "patch": [
                {
                    "op": "replace",
                    "path": "/hierarchy/sites/0/name",
                    "value": "Updated Site",
                }
            ],
            "change_summary": "AI orchestrator initialization adjustments",
            "evidence": ["s3://bucket/path"],
            "actor_id": str(ctx["actor_id"]),
        },
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    body = json.dumps(payload)
    response = client.post(
        "/orchestrator/callbacks",
        data=body,
        headers=_signed_headers(ctx["secret"], body),
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "applied"
    assert data["document_version"] == ctx["document"].current_version
    assert ctx["session"].committed is True
    assert ctx["document"].current_version == 2
    assert (
        ctx["document"].document_data["hierarchy"]["sites"][0]["name"]
        == "Updated Site"
    )
    assert len(ctx["session"].added_objects) == 1
    version = ctx["session"].added_objects[0]
    assert version.version_number == 2
    assert version.patch_operations == payload["data"]["patch"]
    assert version.evidence_uris == payload["data"]["evidence"]
    assert str(version.created_by) == str(ctx["actor_id"])


def test_invalid_signature_rejected(orchestrator_test_context):
    """Requests with invalid signatures are rejected before processing."""

    ctx = orchestrator_test_context
    client = ctx["client"]

    payload = {
        "event": "initialization.completed",
        "data": {
            "document_id": str(ctx["document_id"]),
            "tenant_id": str(ctx["tenant_id"]),
            "document_version": ctx["document"].current_version,
            "patch": [],
        },
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    body = json.dumps(payload)
    headers = {
        "content-type": "application/json",
        orchestrator.SIGNATURE_HEADER: "sha256=invalid",
    }

    response = client.post("/orchestrator/callbacks", data=body, headers=headers)

    assert response.status_code == 400
    assert ctx["session"].committed is False
    assert ctx["document"].current_version == 1
