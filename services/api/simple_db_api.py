#!/usr/bin/env python3
"""
OriginFD API with Simplified Database Integration
"""
import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.dialects.sqlite import CHAR
import uuid
import os

from core.auth import (
    authenticate_user, create_token_pair, verify_password, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
)

# Simple database setup
DATABASE_URL = "sqlite:///./originfd_simple.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Simplified models
class User(Base):
    __tablename__ = "users"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @property
    def roles(self) -> List[str]:
        """Return user roles based on flags and role field."""
        user_roles = []
        if self.is_superuser:
            user_roles.append("admin")
        if self.role:
            user_roles.append(self.role.lower())
        else:
            user_roles.append("user")
        return user_roles

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(CHAR(36), nullable=False, index=True)
    domain = Column(String(50), nullable=False)
    scale = Column(String(50), nullable=False)
    status = Column(String(50), default="DRAFT")
    location_name = Column(String(255), nullable=True)
    total_capacity_kw = Column(String(20), nullable=True)
    version = Column(String(20), default="1.0")
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@originfd.com").first()
        if not admin_user:
            print("Creating initial users...")
            admin_user = User(
                email="admin@originfd.com",
                hashed_password=get_password_hash("admin"),
                full_name="Admin User",
                is_active=True,
                is_superuser=True,
                role="engineer"
            )
            db.add(admin_user)
            
            regular_user = User(
                email="user@originfd.com", 
                hashed_password=get_password_hash("password"),
                full_name="Regular User",
                is_active=True,
                role="user"
            )
            db.add(regular_user)
            db.commit()
            
            print("Creating sample projects...")
            projects = [
                Project(
                    name="Solar Farm Arizona Phase 1",
                    description="Large-scale solar PV installation",
                    owner_id=admin_user.id,
                    domain="PV",
                    scale="UTILITY",
                    status="ACTIVE",
                    location_name="Arizona, USA",
                    total_capacity_kw="500000"
                ),
                Project(
                    name="Commercial BESS Installation",
                    description="Battery energy storage system",
                    owner_id=admin_user.id,
                    domain="BESS", 
                    scale="COMMERCIAL",
                    status="DRAFT",
                    location_name="California, USA",
                    total_capacity_kw="2000"
                ),
                Project(
                    name="Hybrid Microgrid Campus",
                    description="Combined PV + BESS system",
                    owner_id=regular_user.id,
                    domain="HYBRID",
                    scale="INDUSTRIAL", 
                    status="UNDER_REVIEW",
                    location_name="Texas, USA",
                    total_capacity_kw="10000"
                )
            ]
            
            for project in projects:
                db.add(project)
            db.commit()
            print("Database initialized successfully!")
        else:
            print("Database already initialized.")
    except Exception as e:
        db.rollback()
        print(f"Database initialization error: {e}")
        raise
    finally:
        db.close()

# FastAPI app
app = FastAPI(
    title="OriginFD API",
    description="Simplified Database Integration",
    version="0.3.1"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001", "http://localhost:3002",
        "http://localhost:3003", "http://localhost:3004", "http://localhost:3005",
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
    roles: List[str] = ["user"]

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

# Initialize on startup
@app.on_event("startup")
async def startup():
    init_db()

# Routes
@app.get("/")
async def root():
    return {
        "name": "OriginFD API",
        "version": "0.3.1",
        "status": "running",
        "features": ["JWT Authentication", "SQLite Database"]
    }

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "roles": user.roles
    }
    
    access_token, refresh_token = create_token_pair(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    user_id = current_user.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "role": user.role,
        "roles": user.roles,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@app.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    """List all projects (simplified - no auth for now)"""
    projects = db.query(Project).filter(Project.is_archived == False).all()
    
    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "project_name": project.name,
            "domain": project.domain,
            "scale": project.scale,
            "current_version": int(project.version.split('.')[0]) if project.version else 1,
            "content_hash": f"hash-{project.id[:8]}",
            "is_active": project.status not in ["CANCELLED", "DECOMMISSIONED"],
            "created_at": project.created_at.isoformat() + "Z",
            "updated_at": project.updated_at.isoformat() + "Z"
        })
    
    return {"projects": result}

@app.get("/projects/{project_id}")  
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "project_name": project.name,
        "domain": project.domain,
        "scale": project.scale,
        "current_version": int(project.version.split('.')[0]) if project.version else 1,
        "content_hash": f"hash-{project.id[:8]}",
        "is_active": project.status not in ["CANCELLED", "DECOMMISSIONED"],
        "created_at": project.created_at.isoformat() + "Z",
        "updated_at": project.updated_at.isoformat() + "Z"
    }

@app.post("/projects", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest, db: Session = Depends(get_db)):
    """Create new project"""
    # For simplicity, use first user as owner
    first_user = db.query(User).first()
    if not first_user:
        raise HTTPException(status_code=400, detail="No users found")
    
    new_project = Project(
        name=request.project_name,
        description=request.description,
        owner_id=first_user.id,
        domain=request.domain,
        scale=request.scale,
        location_name=request.location
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return ProjectResponse(
        id=new_project.id,
        project_name=new_project.name,
        description=new_project.description,
        domain=new_project.domain,
        scale=new_project.scale,
        current_version=1,
        content_hash=f"hash-{new_project.id[:8]}",
        is_active=True,
        created_at=new_project.created_at.isoformat() + "Z",
        updated_at=new_project.updated_at.isoformat() + "Z"
    )

@app.get("/documents/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get ODL-SD document"""
    project = db.query(Project).filter(Project.id == document_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "meta": {
            "project": project.name,
            "domain": project.domain,
            "scale": project.scale,
            "created_at": project.created_at.isoformat() + "Z",
            "updated_at": project.updated_at.isoformat() + "Z",
            "version": project.version or "v1"
        },
        "content": {
            "description": project.description or f"{project.domain} {project.scale} project",
            "capacity": project.total_capacity_kw + " kW" if project.total_capacity_kw else "TBD",
            "location": project.location_name or "TBD"
        }
    }

if __name__ == "__main__":
    print("Starting OriginFD API with Simple Database...")
    print("Available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Demo credentials: admin@originfd.com / admin")
    
    uvicorn.run(
        "simple_db_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )