"""
models.Project management endpoints.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import httpx



# Simple auth bypass for testing
def get_current_user(*args, **kwargs):
    return {
        "id": "ab9c411c-5c5f-4eb0-8f94-5b998b9dd3fc",
        "email": "admin@originfd.com",
        "tenant_id": "11111111-1111-4111-8111-111111111111",
    }

from deps import get_current_user



from core.config import get_settings


# Temporary mock for testing without auth
def get_mock_user():
    return {
        "id": "ab9c411c-5c5f-4eb0-8f94-5b998b9dd3fc",
        "email": "admin@originfd.com",
        "tenant_id": "11111111-1111-4111-8111-111111111111",
    }


import models
from core.database import SessionDep
from fastapi import APIRouter, Depends, HTTPException, Query, status
from odl_sd.document_generator import DocumentGenerator
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.document import DocumentVersion as SADocumentVersion

# Temporarily disabled due to import issues:
# from services.orchestrator.agents.agent_manager import AgentManager


# Temporary placeholder
class AgentManager:
    @staticmethod
    def detect_bottlenecks(lifecycle_data):
        """Placeholder for bottleneck detection."""
        return []  # TODO: Implement actual bottleneck detection


from models.project import (  # type: ignore  # circular import friendliness
    ProjectDomain as SAProjectDomain,
    ProjectScale as SAProjectScale,
    ProjectStatus as SAProjectStatus,
)


router = APIRouter()


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    domain: SAProjectDomain
    scale: SAProjectScale
    location_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Latitude must be between -90 and 90 degrees"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude must be between -180 and 180 degrees",
    )
    country_code: Optional[str] = Field(
        None, min_length=2, max_length=3, description="ISO country code"
    )
    total_capacity_kw: Optional[float] = Field(
        None, gt=0, description="Capacity must be greater than 0"
    )
    tags: List[str] = Field(default_factory=list, max_items=20)

    class Config:
        str_strip_whitespace = True

    @validator("domain", pre=True)
    def _parse_domain(cls, value: object) -> SAProjectDomain:
        """Normalize incoming domain strings to enum values."""
        if isinstance(value, SAProjectDomain):
            return value
        if isinstance(value, str):
            normalized = value.strip().upper()
            try:
                return SAProjectDomain[normalized]
            except KeyError as exc:  # pragma: no cover - defensive branch
                raise ValueError(f"Unsupported domain '{value}'") from exc
        raise ValueError("Domain must be a string")

    @validator("scale", pre=True)
    def _parse_scale(cls, value: object) -> SAProjectScale:
        """Normalize incoming scale strings to enum values."""
        if isinstance(value, SAProjectScale):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            for candidate in {normalized, normalized.lower(), normalized.upper()}:
                try:
                    return SAProjectScale(candidate.lower())
                except ValueError:
                    try:
                        return SAProjectScale[candidate.upper()]
                    except (AttributeError, KeyError):
                        continue
        raise ValueError("Scale must be a valid project scale value")


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[SAProjectStatus] = None
    location_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Latitude must be between -90 and 90 degrees"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude must be between -180 and 180 degrees",
    )
    total_capacity_kw: Optional[float] = Field(
        None, gt=0, description="Capacity must be greater than 0"
    )
    tags: Optional[List[str]] = Field(None, max_items=20)

    class Config:
        str_strip_whitespace = True


class DocumentMetadata(BaseModel):
    """Summary metadata about a project's associated document."""

    id: str
    content_hash: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Response model for project data."""

    id: str
    name: str
    description: Optional[str]
    domain: SAProjectDomain
    scale: SAProjectScale
    status: SAProjectStatus
    display_status: str
    completion_percentage: int
    location_name: Optional[str]
    total_capacity_kw: Optional[float]
    tags: List[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime
    initialization_task_id: Optional[str] = None
    primary_document_id: Optional[str] = None
    document: Optional[DocumentMetadata] = None
    document_id: Optional[str] = None
    document_hash: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectSummaryResponse(BaseModel):
    """Lightweight project summary for listings."""

    id: str
    name: str
    domain: SAProjectDomain
    scale: SAProjectScale
    status: SAProjectStatus
    display_status: str
    completion_percentage: int
    location_name: Optional[str]
    total_capacity_kw: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Response model for project listings."""

    projects: List[ProjectSummaryResponse]
    total: int
    page: int
    page_size: int


def _get_project_document_metadata(
    db: Session, project_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None
) -> Optional[models.Document]:
    """Return the latest document for a project if available."""

    document_query = db.query(models.Document).filter(
        models.Document.portfolio_id == project_id
    )

    if tenant_id:
        document_query = document_query.filter(models.Document.tenant_id == tenant_id)

    return document_query.order_by(models.Document.created_at.desc()).first()


def _build_document_metadata(document: models.Document) -> DocumentMetadata:
    """Serialize a document ORM instance to response metadata."""

    return DocumentMetadata(
        id=str(document.id),
        content_hash=document.content_hash,
        version=document.current_version,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: Session = Depends(SessionDep),
    # Temporarily disabled for testing: current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[SAProjectDomain] = None,
    status: Optional[SAProjectStatus] = None,
    search: Optional[str] = None,
):
    """
    List projects for the current user.
    """
    # Return all projects for testing (no user filtering)
    query = db.query(models.Project).filter(models.Project.is_archived is False)

    # Apply filters
    if domain:
        query = query.filter(models.Project.domain == domain)

    if status:
        query = query.filter(models.Project.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Project.name.ilike(search_term),
                models.Project.description.ilike(search_term),
                models.Project.location_name.ilike(search_term),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    projects = (
        query.order_by(models.Project.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert to response models
    project_summaries: List[ProjectSummaryResponse] = []
    for project in projects:
        project_summaries.append(
            ProjectSummaryResponse(
                id=str(project.id),
                name=project.name,
                domain=project.domain,
                scale=project.scale,
                status=project.status,
                display_status=project.display_status,
                completion_percentage=project.completion_percentage,
                location_name=project.location_name,
                total_capacity_kw=project.total_capacity_kw,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        )

    return ProjectListResponse(
        projects=project_summaries, total=total, page=page, page_size=page_size
    )


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new project.
    """
    try:
        owner_uuid = uuid.UUID(str(current_user.get("id")))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user identifier for project owner",
        )

    tenant_id_value = current_user.get("tenant_id")
    if not tenant_id_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required to create a project",
        )

    try:
        tenant_uuid = uuid.UUID(str(tenant_id_value))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant identifier",
        ) from exc

    # Generate initial ODL-SD document for the project
    try:
        odl_document = DocumentGenerator.create_project_document(
            project_name=project_data.name,
            domain=project_data.domain.value,
            scale=project_data.scale.name,
            description=project_data.description,
            location=project_data.location_name,
            capacity_kw=project_data.total_capacity_kw,
            user_id=str(owner_uuid),
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate project document: {exc}",
        )

    is_valid, validation_errors = odl_document.validate_document()
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(validation_errors) or "Generated document failed validation",
        )

    document_payload = odl_document.to_dict()
    document_hash = odl_document.meta.versioning.content_hash

    project = models.Project(
        name=project_data.name,
        description=project_data.description,
        domain=project_data.domain,
        scale=project_data.scale,
        location_name=project_data.location_name,
        latitude=project_data.latitude,
        longitude=project_data.longitude,
        country_code=project_data.country_code,
        total_capacity_kw=project_data.total_capacity_kw,
        owner_id=owner_uuid,
        status=SAProjectStatus.DRAFT,
    )
    project.tags_list = project_data.tags

    document = models.Document(
        tenant_id=tenant_uuid,
        project_name=project_data.name,
        portfolio_id=project.id,  # temporary placeholder until flush assigns ID
        domain=project_data.domain.value,
        scale=project_data.scale.name,
        current_version=1,
        content_hash=document_hash,
        document_data=document_payload,
    )

    try:
        db.add(project)
        db.flush()  # Ensure project ID is available for document linkage

        document.portfolio_id = project.id
        db.add(document)
        db.flush()

        project.primary_document_id = document.id

        document_version = SADocumentVersion(
            tenant_id=tenant_uuid,
            document_id=document.id,
            version_number=1,
            content_hash=document_hash,
            change_summary="Initial project document",
            created_by=owner_uuid,
            document_data=document_payload,
        )
        db.add(document_version)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logging.getLogger(__name__).exception(
            "Failed to persist project/document records: %s", exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )

    db.refresh(project)
    db.refresh(document)

    document_metadata = _build_document_metadata(document)

    # Submit initialization task to AI orchestrator
    settings = get_settings()
    task_id: Optional[str] = None
    orchestrator_payload = {
        "task_type": "project_initialization",
        "description": "Initialize project knowledge graph",
        "context": {
            "project_id": str(project.id),
            "project_name": project.name,
            "domain": project.domain.value,
            "scale": project.scale.name,
        },
        "tenant_id": current_user.get("tenant_id"),
        "user_id": current_user.get("id"),
    }

    try:
        async with httpx.AsyncClient(
            base_url=settings.ORCHESTRATOR_URL, timeout=30.0
        ) as client:
            response = await client.post("/tasks/", json=orchestrator_payload)
            response.raise_for_status()
            task_id = response.json().get("task_id")
    except Exception as e:
        logging.getLogger(__name__).error(
            "Failed to submit project initialization task: %s", e
        )

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        domain=project.domain,
        scale=project.scale,
        status=project.status,
        display_status=project.display_status,
        completion_percentage=project.completion_percentage,
        location_name=project.location_name,
        total_capacity_kw=project.total_capacity_kw,
        tags=project.tags_list,
        owner_id=str(project.owner_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
        initialization_task_id=task_id,
        primary_document_id=
            str(project.primary_document_id) if project.primary_document_id else None,
        document=document_metadata,
        document_id=str(document.id),
        document_hash=document_hash,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific project by ID.
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID format"
        )

    project = (
        db.query(models.Project)
        .filter(
            and_(models.Project.id == project_uuid, models.Project.is_archived is False)
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="models.Project not found or archived",
        )

    # Check if user has access to this project
    if not project.can_edit(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    try:
        tenant_uuid = (
            uuid.UUID(str(current_user.get("tenant_id")))
            if current_user.get("tenant_id")
            else None
        )
    except (TypeError, ValueError):
        tenant_uuid = None

    document = _get_project_document_metadata(db, project.id, tenant_uuid)
    document_metadata = _build_document_metadata(document) if document else None

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        domain=project.domain,
        scale=project.scale,
        status=project.status,
        display_status=project.display_status,
        completion_percentage=project.completion_percentage,
        location_name=project.location_name,
        total_capacity_kw=project.total_capacity_kw,
        tags=project.tags_list,
        owner_id=str(project.owner_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
        primary_document_id=
            str(project.primary_document_id) if project.primary_document_id else None,
        document=document_metadata,
        document_id=str(document.id) if document else None,
        document_hash=document.content_hash if document else None,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a specific project.
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID format"
        )

    project = (
        db.query(models.Project)
        .filter(
            and_(models.Project.id == project_uuid, models.Project.is_archived is False)
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="models.Project not found or archived",
        )

    # Check if user has edit access
    if not project.can_edit(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Update fields
    update_data = project_data.dict(exclude_unset=True)

    if "tags" in update_data:
        project.tags_list = update_data.pop("tags") or []

    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(project)

    try:
        tenant_uuid = (
            uuid.UUID(str(current_user.get("tenant_id")))
            if current_user.get("tenant_id")
            else None
        )
    except (TypeError, ValueError):
        tenant_uuid = None

    document = _get_project_document_metadata(db, project.id, tenant_uuid)
    document_metadata = _build_document_metadata(document) if document else None

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        domain=project.domain,
        scale=project.scale,
        status=project.status,
        display_status=project.display_status,
        completion_percentage=project.completion_percentage,
        location_name=project.location_name,
        total_capacity_kw=project.total_capacity_kw,
        tags=project.tags_list,
        owner_id=str(project.owner_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
        primary_document_id=
            str(project.primary_document_id) if project.primary_document_id else None,
        document=document_metadata,
        document_id=str(document.id) if document else None,
        document_hash=document.content_hash if document else None,
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Soft delete a specific project (archive it).
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID format"
        )

    project = (
        db.query(models.Project)
        .filter(
            and_(models.Project.id == project_uuid, models.Project.is_archived is False)
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="models.Project not found or already archived",
        )

    # Check if user has delete access (only owner for now)
    if str(project.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete project",
        )

    # Soft delete by setting archived flag
    project.is_archived = True
    project.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "models.Project archived successfully"}


@router.get("/stats/summary")
async def get_project_stats(
    db: Session = Depends(SessionDep), current_user: dict = Depends(get_current_user)
):
    """
    Get project statistics for the current user.
    """
    user_id = current_user["id"]

    # Total projects (excluding archived)
    total_projects = (
        db.query(models.Project)
        .filter(
            and_(
                models.Project.owner_id == user_id, models.Project.is_archived is False
            )
        )
        .count()
    )

    # Active projects (excluding archived)
    active_projects = (
        db.query(models.Project)
        .filter(
            and_(
                models.Project.owner_id == user_id,
                models.Project.status == models.models.ProjectStatus.ACTIVE,
                models.Project.is_archived is False,
            )
        )
        .count()
    )

    # models.Projects by domain (excluding archived)
    pv_projects = (
        db.query(models.Project)
        .filter(
            and_(
                models.Project.owner_id == user_id,
                models.Project.domain == models.models.ProjectDomain.PV,
                models.Project.is_archived is False,
            )
        )
        .count()
    )

    bess_projects = (
        db.query(models.Project)
        .filter(
            and_(
                models.Project.owner_id == user_id,
                models.Project.domain == models.models.ProjectDomain.BESS,
                models.Project.is_archived is False,
            )
        )
        .count()
    )

    hybrid_projects = (
        db.query(models.Project)
        .filter(
            and_(
                models.Project.owner_id == user_id,
                models.Project.domain == models.models.ProjectDomain.HYBRID,
                models.Project.is_archived is False,
            )
        )
        .count()
    )

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "pv_projects": pv_projects,
        "bess_projects": bess_projects,
        "hybrid_projects": hybrid_projects,
    }


def _serialize_gate(
    gate: "models.LifecycleGate",
    approval: Optional["models.LifecycleGateApproval"] = None,
) -> dict:
    """Serialize a lifecycle gate with approval metadata."""

    approval_obj = approval if approval is not None else getattr(gate, "approval", None)
    approval_payload = approval_obj.as_dict() if approval_obj else None

    payload = {
        "id": str(gate.id),
        "name": gate.name,
        "status": gate.status,
        "sequence": gate.sequence,
        "description": gate.description,
        "due_date": gate.due_date.isoformat() if gate.due_date else None,
        "owner": gate.owner,
        "metadata": gate.context_dict(),
        "approval": approval_payload,
        "approval_status": approval_payload["status"] if approval_payload else "pending",
    }

    return payload


def _serialize_phase(
    phase: "models.LifecyclePhase",
    gates: Optional[List[dict]] = None,
) -> dict:
    """Serialize a lifecycle phase with ordered gates."""

    if gates is None:
        gates = [_serialize_gate(gate) for gate in sorted(phase.gates, key=lambda gate: gate.sequence)]
    return {
        "id": str(phase.id),
        "name": phase.name,
        "status": phase.status,
        "sequence": phase.sequence,
        "description": phase.description,
        "metadata": phase.context_dict(),
        "gates": gates,
    }


def _fetch_project_lifecycle_rows(db: Session, project_uuid: uuid.UUID):
    """Return phase, gate, approval rows for lifecycle serialization."""

    return (
        db.query(
            models.LifecyclePhase,
            models.LifecycleGate,
            models.LifecycleGateApproval,
        )
        .outerjoin(
            models.LifecycleGate,
            models.LifecycleGate.phase_id == models.LifecyclePhase.id,
        )
        .outerjoin(
            models.LifecycleGateApproval,
            models.LifecycleGateApproval.gate_id == models.LifecycleGate.id,
        )
        .filter(models.LifecyclePhase.project_id == project_uuid)
        .order_by(models.LifecyclePhase.sequence, models.LifecycleGate.sequence)
        .all()
    )


@router.get("/{project_id}/lifecycle")
async def get_project_lifecycle(
    project_id: str,
    db: SessionDep,
    current_user: dict = Depends(get_current_user),
):
    """Return lifecycle phases and gate checklist for a project."""

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail="Project not found") from exc

    rows = _fetch_project_lifecycle_rows(db, project_uuid)

    phase_cache: dict[uuid.UUID, tuple["models.LifecyclePhase", dict]] = {}

    for phase, gate, approval in rows:
        if phase.id not in phase_cache:
            phase_cache[phase.id] = (phase, _serialize_phase(phase, gates=[]))

        phase_payload = phase_cache[phase.id][1]

        if gate is not None:
            phase_payload["gates"].append(_serialize_gate(gate, approval))

    if phase_cache:
        ordered_phases = [
            entry[1] for entry in sorted(
                phase_cache.values(), key=lambda item: item[0].sequence
            )
        ]

        for phase_payload in ordered_phases:
            phase_payload["gates"].sort(key=lambda gate_payload: gate_payload["sequence"])
    else:
        phases_only = (
            db.query(models.LifecyclePhase)
            .filter(models.LifecyclePhase.project_id == project_uuid)
            .order_by(models.LifecyclePhase.sequence)
            .all()
        )
        ordered_phases = [_serialize_phase(phase) for phase in phases_only]

    lifecycle_data = {"phases": ordered_phases}

    # Use orchestrator to detect bottlenecks and annotate gates
    bottlenecks = AgentManager.detect_bottlenecks(lifecycle_data)
    lifecycle_data["bottlenecks"] = bottlenecks

    return lifecycle_data
