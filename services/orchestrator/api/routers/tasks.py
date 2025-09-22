"""Task routing for the orchestrator service."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Possible lifecycle states for an accepted task."""

    QUEUED = "queued"


class ProjectContext(BaseModel):
    """Context payload emitted by ``POST /projects`` when seeding a task."""

    project_id: UUID = Field(..., description="Unique identifier for the project")
    project_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    scale: str = Field(..., min_length=1, max_length=255)

    @field_validator("project_name", "domain", "scale")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        """Ensure string fields are normalized and non-empty."""

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty")
        return cleaned


class TaskCreateRequest(BaseModel):
    """Incoming task payload used by other services."""

    task_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    context: ProjectContext
    tenant_id: UUID = Field(..., description="Tenant identifier scoped to the task")
    user_id: UUID = Field(..., description="User initiating the task")

    @field_validator("task_type", mode="before")
    @classmethod
    def _normalize_task_type(cls, value: object) -> str:
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("task_type cannot be empty")
            return cleaned
        raise ValueError("task_type must be a string")

    @field_validator("description", mode="before")
    @classmethod
    def _normalize_description(cls, value: Optional[object]) -> Optional[str]:
        if value is None:
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        raise ValueError("description must be a string if provided")


class TaskRecord(BaseModel):
    """Persisted task information."""

    id: UUID
    task_type: str
    description: Optional[str]
    context: ProjectContext
    tenant_id: UUID
    user_id: UUID
    status: TaskStatus
    created_at: datetime


class TaskAcceptedResponse(BaseModel):
    """Response returned when a task is accepted for processing."""

    task_id: UUID
    status: TaskStatus


class InMemoryTaskStore:
    """Very small in-memory persistence layer used for testing."""

    def __init__(self) -> None:
        self._tasks: Dict[UUID, TaskRecord] = {}

    def add(self, task: TaskRecord) -> TaskRecord:
        self._tasks[task.id] = task
        return task

    def list(self) -> List[TaskRecord]:
        return list(self._tasks.values())

    def clear(self) -> None:
        self._tasks.clear()


task_store = InMemoryTaskStore()
router = APIRouter()


@router.get("/")
async def list_tasks() -> Dict[str, List[TaskRecord]]:
    """List tasks accepted by the orchestrator."""

    return {"tasks": task_store.list()}


@router.post("/", response_model=TaskAcceptedResponse, status_code=201)
async def create_task(task: TaskCreateRequest) -> TaskAcceptedResponse:
    """Accept a new task submission from dependent services."""

    record = TaskRecord(
        id=uuid4(),
        task_type=task.task_type,
        description=task.description,
        context=task.context,
        tenant_id=task.tenant_id,
        user_id=task.user_id,
        status=TaskStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
    )
    task_store.add(record)
    return TaskAcceptedResponse(task_id=record.id, status=record.status)
