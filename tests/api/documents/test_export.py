import os
import sys
import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest
import yaml
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
from api.utils.document_serialization import canonicalize_document  # noqa: E402
from core.database import SessionDep  # noqa: E402
from deps import get_current_user  # noqa: E402
import models  # noqa: E402


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class FakeSession:
    def __init__(self, document):
        self.document = document

    def query(self, model):
        if model is models.Document:
            return FakeQuery(self.document)
        return FakeQuery(None)


@pytest.fixture()
def sample_document():
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "$schema": "https://odl-sd.org/schemas/v4.1/document.json",
        "schema_version": "4.1",
        "meta": {
            "project": "Demo Export",
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
                "content_hash": "sha256:export",
            },
        },
        "hierarchy": {"sites": [{"id": "site-1"}]},
        "requirements": {},
        "libraries": {},
        "instances": [],
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
def test_client(sample_document):
    app = FastAPI()
    app.include_router(documents.router, prefix="/documents")

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    document = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        project_name=sample_document["meta"]["project"],
        portfolio_id=None,
        domain=sample_document["meta"]["domain"],
        scale=sample_document["meta"]["scale"],
        current_version=1,
        content_hash=sample_document["meta"]["versioning"]["content_hash"],
        document_data=sample_document,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True,
    )

    fake_session = FakeSession(document)

    app.dependency_overrides[SessionDep] = lambda: fake_session
    app.dependency_overrides[get_current_user] = lambda: {
        "id": str(user_id),
        "tenant_id": str(tenant_id),
    }

    client = TestClient(app)
    client.document = document  # type: ignore[attr-defined]
    return client


def test_export_document_json(test_client, sample_document):
    response = test_client.get(f"/documents/{test_client.document.id}/export?format=json")

    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith("_odl.json")
    expected = canonicalize_document(sample_document)
    assert response.json() == expected


def test_export_document_yaml(test_client, sample_document):
    response = test_client.get(f"/documents/{test_client.document.id}/export?format=yaml")

    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith("_odl.yaml")

    exported = yaml.safe_load(response.text)
    expected = canonicalize_document(sample_document)
    assert exported == expected
