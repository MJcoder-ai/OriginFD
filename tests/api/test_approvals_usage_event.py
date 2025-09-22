import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

from api.routers import approvals  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    app = FastAPI()
    app.include_router(approvals.router, prefix="/approvals")

    publish_calls = []

    def _record_usage(tenant: str, psu: int, metadata: dict | None = None):
        publish_calls.append({
            "tenant_id": tenant,
            "psu": psu,
            "metadata": metadata or {},
        })
        return {"psu": psu, "fee": 0}

    monkeypatch.setattr(approvals, "publish_usage_event", _record_usage)

    client = TestClient(app)
    client.publish_calls = publish_calls  # type: ignore[attr-defined]
    return client


def test_gate_approval_publishes_usage_event(client):
    payload = {
        "project_id": "proj-123",
        "decision": "approve",
        "source": {"tenant_id": "11111111-1111-4111-8111-111111111111"},
        "target": {"phase": "design"},
    }

    response = client.post("/approvals/", json=payload)

    assert response.status_code == 200
    assert client.publish_calls  # type: ignore[attr-defined]
    usage_call = client.publish_calls[0]  # type: ignore[index]
    assert usage_call["tenant_id"] == payload["source"]["tenant_id"]
    assert usage_call["psu"] > 0
    assert usage_call["metadata"]["event"] == "gate_approval"
    assert usage_call["metadata"]["decision"] == payload["decision"]
    assert usage_call["metadata"]["project_id"] == payload["project_id"]
