"""
Project management endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from core.database import SessionDep
from models.project import Project, ProjectDomain, ProjectScale, ProjectStatus
from models.user import User
from api.routers.auth import get_current_user

router = APIRouter()


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    domain: ProjectDomain
    scale: ProjectScale
    location_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[str] = Field(None, max_length=20)
    longitude: Optional[str] = Field(None, max_length=20)
    country_code: Optional[str] = Field(None, max_length=3)
    total_capacity_kw: Optional[str] = Field(None, max_length=20)
    tags: List[str] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatus] = None
    location_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[str] = Field(None, max_length=20)
    longitude: Optional[str] = Field(None, max_length=20)
    total_capacity_kw: Optional[str] = Field(None, max_length=20)
    tags: Optional[List[str]] = None


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
    total_capacity_kw: Optional[str]
    tags: List[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime

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
    total_capacity_kw: Optional[str]
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
    query = db.query(Project).filter(Project.owner_id == current_user["id"])
    
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
                Project.location_name.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    projects = query.order_by(Project.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert to response models
    project_summaries = []
    for project in projects:
        project_summaries.append(ProjectSummaryResponse(
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
            updated_at=project.updated_at
        ))
    
    return ProjectListResponse(
        projects=project_summaries,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
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
        status=ProjectStatus.DRAFT
    )
    
    db.add(project)
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
        updated_at=project.updated_at
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific project by ID.
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    project = db.query(Project).filter(Project.id == project_uuid).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to this project
    if not project.can_edit(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
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
        updated_at=project.updated_at
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a specific project.
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    project = db.query(Project).filter(Project.id == project_uuid).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has edit access
    if not project.can_edit(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    
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
        updated_at=project.updated_at
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific project.
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format"
        )
    
    project = db.query(Project).filter(Project.id == project_uuid).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has delete access (only owner for now)
    if str(project.owner_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete project"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/stats/summary")
async def get_project_stats(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Get project statistics for the current user.
    """
    user_id = current_user["id"]
    
    # Total projects
    total_projects = db.query(Project).filter(Project.owner_id == user_id).count()
    
    # Active projects
    active_projects = db.query(Project).filter(
        and_(Project.owner_id == user_id, Project.status == ProjectStatus.ACTIVE)
    ).count()
    
    # Projects by domain
    pv_projects = db.query(Project).filter(
        and_(Project.owner_id == user_id, Project.domain == ProjectDomain.PV)
    ).count()
    
    bess_projects = db.query(Project).filter(
        and_(Project.owner_id == user_id, Project.domain == ProjectDomain.BESS)
    ).count()
    
    hybrid_projects = db.query(Project).filter(
        and_(Project.owner_id == user_id, Project.domain == ProjectDomain.HYBRID)
    ).count()
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "pv_projects": pv_projects,
        "bess_projects": bess_projects,
        "hybrid_projects": hybrid_projects,
    }