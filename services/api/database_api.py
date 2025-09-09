#!/usr/bin/env python3
"""
OriginFD API with Real Database Integration
"""
import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import get_db, init_database, SessionDep
from core.dependencies import CurrentUser, AdminUser, EngineerUser
from models.user import User
from models.project import Project, ProjectDomain, ProjectScale, ProjectStatus
from core.auth import authenticate_user, create_token_pair, ACCESS_TOKEN_EXPIRE_MINUTES

# FastAPI app
app = FastAPI(
    title="OriginFD API",
    description="Real Database Integration with JWT Authentication",
    version="0.3.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    roles: list[str] = ["user"]

class ProjectCreateRequest(BaseModel):
    project_name: str
    description: Optional[str] = None
    domain: str
    scale: str
    location: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    project_name: str
    description: Optional[str]
    domain: str
    scale: str
    current_version: int
    content_hash: str
    is_active: bool
    created_at: str
    updated_at: str

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("Initializing database...")
    try:
        init_database()
        print("Database initialization complete!")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# Basic endpoints
@app.get("/")
async def root():
    return {
        "name": "OriginFD API",
        "version": "0.3.0",
        "status": "running",
        "features": ["JWT Authentication", "Real Database", "Role-based Access Control"]
    }

@app.get("/health")
async def health(db: SessionDep):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected", "auth": "enabled"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")

# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, db: SessionDep):
    """Login with email and password"""
    # Get user from database
    user = db.query(User).filter(User.email == login_request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    from core.auth import verify_password
    if not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Update last login
    user.update_last_login()
    db.commit()
    
    # Create token data
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "roles": user.roles
    }
    
    # Create token pair
    access_token, refresh_token = create_token_pair(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: CurrentUser):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["id"]),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        is_active=current_user["is_active"],
        roles=current_user["roles"]
    )

@app.post("/auth/logout")
async def logout(current_user: CurrentUser):
    """Logout current user"""
    # In a real implementation, you'd invalidate the token in the database
    return {"message": "Successfully logged out"}

# Project endpoints
@app.get("/projects")
async def list_projects(
    current_user: CurrentUser,
    db: SessionDep,
    skip: int = 0,
    limit: int = 20
):
    """List user's projects"""
    user_id = current_user["id"]
    
    # Get projects owned by the user (later we'll add shared projects)
    projects = (
        db.query(Project)
        .filter(Project.owner_id == user_id)
        .filter(Project.is_archived == False)
        .order_by(desc(Project.updated_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert to API response format
    project_list = []
    for project in projects:
        project_list.append({
            "id": str(project.id),
            "project_name": project.name,
            "domain": project.domain.value,
            "scale": project.scale.value,
            "current_version": int(project.version.split('.')[0]) if project.version else 1,
            "content_hash": f"hash-{project.id}",
            "is_active": project.status not in [ProjectStatus.CANCELLED, ProjectStatus.DECOMMISSIONED],
            "created_at": project.created_at.isoformat() + "Z",
            "updated_at": project.updated_at.isoformat() + "Z"
        })
    
    return {"projects": project_list}

@app.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    db: SessionDep
):
    """Get specific project"""
    user_id = current_user["id"]
    
    # Get project and verify access
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access (owner or team member)
    if project.owner_id != user_id:
        # TODO: Check team membership
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(project.id),
        "project_name": project.name,
        "domain": project.domain.value,
        "scale": project.scale.value,
        "current_version": int(project.version.split('.')[0]) if project.version else 1,
        "content_hash": f"hash-{project.id}",
        "is_active": project.status not in [ProjectStatus.CANCELLED, ProjectStatus.DECOMMISSIONED],
        "created_at": project.created_at.isoformat() + "Z",
        "updated_at": project.updated_at.isoformat() + "Z"
    }

@app.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreateRequest, 
    current_user: EngineerUser,
    db: SessionDep
):
    """Create new project (requires engineer role)"""
    user_id = current_user["id"]
    
    try:
        # Create new project
        new_project = Project(
            name=project_data.project_name,
            description=project_data.description,
            owner_id=user_id,
            domain=ProjectDomain(project_data.domain),
            scale=ProjectScale(project_data.scale),
            status=ProjectStatus.DRAFT,
            location_name=project_data.location
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        return ProjectResponse(
            id=str(new_project.id),
            project_name=new_project.name,
            description=new_project.description,
            domain=new_project.domain.value,
            scale=new_project.scale.value,
            current_version=1,
            content_hash=f"hash-{new_project.id}",
            is_active=True,
            created_at=new_project.created_at.isoformat() + "Z",
            updated_at=new_project.updated_at.isoformat() + "Z"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create project: {str(e)}"
        )

@app.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    db: SessionDep
):
    """Get ODL-SD document"""
    user_id = current_user["id"]
    
    # Get project and verify access
    project = db.query(Project).filter(Project.id == document_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if project.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Return ODL-SD document structure
    return {
        "meta": {
            "project": project.name,
            "domain": project.domain.value,
            "scale": project.scale.value,
            "created_at": project.created_at.isoformat() + "Z",
            "updated_at": project.updated_at.isoformat() + "Z",
            "version": project.version or "v1"
        },
        "content": {
            "description": project.description or f"{project.domain.value} {project.scale.value} project",
            "capacity": project.total_capacity_kw + " kW" if project.total_capacity_kw else "TBD",
            "location": project.location_name or "TBD"
        }
    }

# Scenario audit storage
class ScenarioAudit(BaseModel):
    id: Optional[str] = None
    project_id: str
    name: str
    irr_percent: float
    lcoe_per_kwh: float
    npv_usd: float
    created_at: Optional[str] = None


scenario_audit_log: List[ScenarioAudit] = []


@app.post("/scenarios", response_model=ScenarioAudit)
async def store_scenario_audit(scenario: ScenarioAudit, current_user: CurrentUser):
    record = ScenarioAudit(
        id=scenario.id or str(uuid4()),
        project_id=scenario.project_id,
        name=scenario.name,
        irr_percent=scenario.irr_percent,
        lcoe_per_kwh=scenario.lcoe_per_kwh,
        npv_usd=scenario.npv_usd,
        created_at=datetime.utcnow().isoformat(),
    )
    scenario_audit_log.append(record)
    return record

# Admin endpoints
@app.get("/admin/stats")
async def get_admin_stats(admin_user: AdminUser, db: SessionDep):
    """Get admin statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(
        Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.UNDER_REVIEW, ProjectStatus.APPROVED])
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "system_status": "healthy"
    }


if __name__ == "__main__":
    print("Starting OriginFD API with Real Database Integration...")
    print("Available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Demo credentials:")
    print("  Admin: admin@originfd.com / admin")
    print("  User:  user@originfd.com / password")
    
    uvicorn.run(
        "database_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )