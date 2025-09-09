"""
Project management endpoints.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import httpx
from api.routers.auth import get_current_user
from core.config import get_settings
from core.database import SessionDep
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.project import Project, ProjectDomain, ProjectScale, ProjectStatus
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from services.orchestrator.agents.agent_manager import AgentManager

router = APIRouter()


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    domain: ProjectDomain
    scale: ProjectScale
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


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatus] = None
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


class ProjectResponse(BaseModel):
    """Response model for project data."""

    id: str
    name: str
    description: Optional[str]
    domain: ProjectDomain
    scale: ProjectScale
    status: ProjectStatus
    display_status: str
    completion_percentage: int
    location_name: Optional[str]
    total_capacity_kw: Optional[float]
    tags: List[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime
    initialization_task_id: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectSummaryResponse(BaseModel):
    """Lightweight project summary for listings."""

    id: str
    name: str
    domain: ProjectDomain
    scale: ProjectScale
    status: ProjectStatus
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


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[ProjectDomain] = None,
    status: Optional[ProjectStatus] = None,
    search: Optional[str] = None,
):
    """
    List projects for the current user.
    """
    query = db.query(Project).filter(
        and_(Project.owner_id == current_user["id"], Project.is_archived == False)
    )

    # Apply filters
    if domain:
        query = query.filter(Project.domain == domain)

    if status:
        query = query.filter(Project.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term),
                Project.location_name.ilike(search_term),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    projects = (
        query.order_by(Project.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert to response models
    project_summaries = []
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
    # Create new project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        domain=project_data.domain,
        scale=project_data.scale,
        location_name=project_data.location_name,
        latitude=project_data.latitude,
        longitude=project_data.longitude,
        country_code=project_data.country_code,
        total_capacity_kw=project_data.total_capacity_kw,
        tags=project_data.tags,
        owner_id=current_user["id"],
        status=ProjectStatus.DRAFT,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    # Submit initialization task to AI orchestrator
    settings = get_settings()
    task_id: Optional[str] = None
    orchestrator_payload = {
        "task_type": "project_initialization",
        "description": "Initialize project knowledge graph",
        "context": {
            "project_id": str(project.id),
            "project_name": project.name,
            "domain": (
                project.domain.value
                if hasattr(project.domain, "value")
                else project.domain
            ),
            "scale": (
                project.scale.value
                if hasattr(project.scale, "value")
                else project.scale
            ),
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
        tags=project.tags or [],
        owner_id=str(project.owner_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
        initialization_task_id=task_id,
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
        db.query(Project)
        .filter(and_(Project.id == project_uuid, Project.is_archived == False))
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or archived",
        )

    # Check if user has access to this project
    if not project.can_edit(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
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
        tags=project.tags or [],
        owner_id=str(project.owner_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
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
        db.query(Project)
        .filter(and_(Project.id == project_uuid, Project.is_archived == False))
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or archived",
        )

    # Check if user has edit access
    if not project.can_edit(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Update fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(project)

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
        tags=project.tags or [],
        owner_id=str(project.owner_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
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
        db.query(Project)
        .filter(and_(Project.id == project_uuid, Project.is_archived == False))
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or already archived",
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

    return {"message": "Project archived successfully"}


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
        db.query(Project)
        .filter(and_(Project.owner_id == user_id, Project.is_archived == False))
        .count()
    )

    # Active projects (excluding archived)
    active_projects = (
        db.query(Project)
        .filter(
            and_(
                Project.owner_id == user_id,
                Project.status == ProjectStatus.ACTIVE,
                Project.is_archived == False,
            )
        )
        .count()
    )

    # Projects by domain (excluding archived)
    pv_projects = (
        db.query(Project)
        .filter(
            and_(
                Project.owner_id == user_id,
                Project.domain == ProjectDomain.PV,
                Project.is_archived == False,
            )
        )
        .count()
    )

    bess_projects = (
        db.query(Project)
        .filter(
            and_(
                Project.owner_id == user_id,
                Project.domain == ProjectDomain.BESS,
                Project.is_archived == False,
            )
        )
        .count()
    )

    hybrid_projects = (
        db.query(Project)
        .filter(
            and_(
                Project.owner_id == user_id,
                Project.domain == ProjectDomain.HYBRID,
                Project.is_archived == False,
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


@router.get("/{project_id}/lifecycle")
async def get_project_lifecycle(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return lifecycle phases and gate checklist for a project.

    This temporary implementation returns mock data and uses the
    orchestrator to annotate gates with potential bottlenecks.
    """

    # In a real implementation this data would come from the database
    # or project documents. We provide a minimal structure for now.
    lifecycle_data = {
        "phases": [
            {
                "id": "design",
                "name": "Design",
                "status": "completed",
                "gates": [
                    {"id": "site_assessment", "name": "Site Assessment", "status": "completed"},
                    {"id": "bom_approval", "name": "BOM Approval", "status": "completed"},
                ],
            },
            {
                "id": "procurement",
                "name": "Procurement",
                "status": "current",
                "gates": [
                    {"id": "supplier_selection", "name": "Supplier Selection", "status": "blocked"},
                    {
                        "id": "contract_signed",
                        "name": "Contract Signed",
                        "status": "pending",
                        "due_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                    },
                ],
            },
            {
                "id": "construction",
                "name": "Construction",
                "status": "upcoming",
                "gates": [
                    {"id": "mobilization", "name": "Mobilization", "status": "pending"}
                ],
            },
        ]
    }

    # Use orchestrator to detect bottlenecks and annotate gates
    bottlenecks = AgentManager.detect_bottlenecks(lifecycle_data)
    lifecycle_data["bottlenecks"] = bottlenecks

    return lifecycle_data
