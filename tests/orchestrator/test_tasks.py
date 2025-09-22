"""Tests for the orchestrator task ingestion endpoint."""

from pathlib import Path
import sys
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.orchestrator.api.routers import tasks


def _client() -> TestClient:
    """Create a lightweight FastAPI app mounting the task router."""

    app = FastAPI()
    app.include_router(tasks.router, prefix="/tasks")
    return TestClient(app)


def _project_task_payload() -> dict:
    """Return a payload shaped like the project creation hook emits."""

    return {
        "task_type": "project_initialization",
        "description": "Initialize project knowledge graph",
        "context": {
            "project_id": str(uuid4()),
            "project_name": "Demo Solar Farm",
            "domain": "solar",
            "scale": "UTILITY",
        },
        "tenant_id": str(uuid4()),
        "user_id": str(uuid4()),
    }


def test_create_task_accepts_project_payload() -> None:
    """A project initialization payload should be accepted and persisted."""

    client = _client()
    tasks.task_store.clear()

    payload = _project_task_payload()
    response = client.post("/tasks/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert "task_id" in data

    list_response = client.get("/tasks/")
    stored_tasks = list_response.json()["tasks"]
    assert len(stored_tasks) == 1
    stored_task = stored_tasks[0]
    assert stored_task["context"]["project_id"] == payload["context"]["project_id"]
    assert stored_task["task_type"] == payload["task_type"]


def test_create_task_requires_project_context() -> None:
    """Missing critical context fields should return a validation error."""

    client = _client()
    tasks.task_store.clear()

    payload = _project_task_payload()
    payload["context"].pop("project_id")

    response = client.post("/tasks/", json=payload)

    assert response.status_code == 422
