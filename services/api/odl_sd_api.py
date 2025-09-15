#!/usr/bin/env python3
"""
OriginFD API with ODL-SD Document Generation
"""
import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.dialects.sqlite import CHAR
import uuid
import os
import json

from core.auth import (
    authenticate_user, create_token_pair, verify_password, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
)
from odl_sd.document_generator import DocumentGenerator
from odl_sd.schemas import OdlSdDocument

# Simple Component API router
try:
    from simple_components import router as components_router
    COMPONENTS_AVAILABLE = True
    print("[SUCCESS] Simple components module loaded successfully")
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"Warning: Simple components not available: {e}")

# Simple database setup
DATABASE_URL = "sqlite:///./originfd_odl.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enhanced models with ODL-SD document storage
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
    # ODL-SD document storage
    odl_document = Column(Text, nullable=True)  # JSON string of ODL-SD document
    document_hash = Column(String(255), nullable=True)  # Document content hash
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(CHAR(36), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)
    odl_document = Column(Text, nullable=False)  # JSON string of ODL-SD document
    document_hash = Column(String(255), nullable=False)
    created_by = Column(CHAR(36), nullable=False)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database with enhanced ODL-SD support
def init_db():
    print("Creating database tables with ODL-SD support...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
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

            print("Creating sample projects with ODL-SD documents...")
            projects_data = [
                {
                    "name": "Solar Farm Arizona Phase 1",
                    "description": "Large-scale solar PV installation",
                    "domain": "PV",
                    "scale": "UTILITY",
                    "location": "Arizona, USA",
                    "capacity": 500000.0
                },
                {
                    "name": "Commercial BESS Installation",
                    "description": "Battery energy storage system",
                    "domain": "BESS",
                    "scale": "COMMERCIAL",
                    "location": "California, USA",
                    "capacity": 2000.0
                },
                {
                    "name": "Hybrid Microgrid Campus",
                    "description": "Combined PV + BESS system",
                    "domain": "HYBRID",
                    "scale": "INDUSTRIAL",
                    "location": "Texas, USA",
                    "capacity": 10000.0
                }
            ]

            for i, proj_data in enumerate(projects_data):
                # Generate ODL-SD document
                odl_doc = DocumentGenerator.create_project_document(
                    project_name=proj_data["name"],
                    domain=proj_data["domain"],
                    scale=proj_data["scale"],
                    description=proj_data["description"],
                    location=proj_data["location"],
                    capacity_kw=proj_data["capacity"],
                    user_id=admin_user.id if i < 2 else regular_user.id
                )

                project = Project(
                    name=proj_data["name"],
                    description=proj_data["description"],
                    owner_id=admin_user.id if i < 2 else regular_user.id,
                    domain=proj_data["domain"],
                    scale=proj_data["scale"],
                    status="ACTIVE" if i == 0 else "DRAFT" if i == 1 else "UNDER_REVIEW",
                    location_name=proj_data["location"],
                    total_capacity_kw=str(proj_data["capacity"]),
                    odl_document=json.dumps(odl_doc.to_dict(), indent=2),
                    document_hash=odl_doc.meta.versioning.content_hash
                )
                db.add(project)

            db.commit()
            print("Database initialized successfully with ODL-SD documents!")
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
    description="ODL-SD Document Generation & Validation",
    version="0.4.0"
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

# Include component router if available
if COMPONENTS_AVAILABLE:
    app.include_router(components_router, prefix="/components", tags=["components"])
    print("[SUCCESS] Component API routes registered at /components")

    # Debug endpoint to test router integration
    @app.get("/debug/components-test")
    async def test_components():
        return {"status": "Components router integrated successfully", "available": True}
else:
    print("[WARNING] Component API routes not available")

    @app.get("/debug/components-test")
    async def test_components():
        return {"status": "Components router not available", "available": False}

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
    capacity_kw: Optional[float] = None

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

class DocumentValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    document_hash: str
    schema_version: str

# Initialize on startup
@app.on_event("startup")
async def startup():
    init_db()

# Routes
@app.get("/")
async def root():
    return {
        "name": "OriginFD API",
        "version": "0.4.0",
        "status": "running",
        "features": ["JWT Authentication", "SQLite Database", "ODL-SD v4.1 Documents", "Schema Validation"]
    }

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "odl_sd": "v4.1"}
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

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    user = db.query(User).filter(User.id == current_user["sub"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=user.roles
    )

@app.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    """List all projects with ODL-SD document status"""
    projects = db.query(Project).filter(Project.is_archived == False).all()

    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "project_name": project.name,
            "domain": project.domain,
            "scale": project.scale,
            "current_version": int(project.version.split('.')[0]) if project.version else 1,
            "content_hash": project.document_hash[:8] if project.document_hash else "no-hash",
            "is_active": project.status not in ["CANCELLED", "DECOMMISSIONED"],
            "has_odl_document": bool(project.odl_document),
            "created_at": project.created_at.isoformat() + "Z",
            "updated_at": project.updated_at.isoformat() + "Z"
        })

    return {"projects": result}

@app.get("/projects/{project_id}")
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get specific project with ODL-SD document info"""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "project_name": project.name,
        "domain": project.domain,
        "scale": project.scale,
        "current_version": int(project.version.split('.')[0]) if project.version else 1,
        "content_hash": project.document_hash[:8] if project.document_hash else "no-hash",
        "is_active": project.status not in ["CANCELLED", "DECOMMISSIONED"],
        "has_odl_document": bool(project.odl_document),
        "created_at": project.created_at.isoformat() + "Z",
        "updated_at": project.updated_at.isoformat() + "Z"
    }

@app.post("/projects", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest, db: Session = Depends(get_db)):
    """Create new project with ODL-SD document generation"""
    # For simplicity, use first user as owner
    first_user = db.query(User).first()
    if not first_user:
        raise HTTPException(status_code=400, detail="No users found")

    # Generate ODL-SD document
    odl_doc = DocumentGenerator.create_project_document(
        project_name=request.project_name,
        domain=request.domain,
        scale=request.scale,
        description=request.description,
        location=request.location,
        capacity_kw=request.capacity_kw,
        user_id=first_user.id
    )

    # Validate the generated document
    is_valid, errors = odl_doc.validate_document()
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Generated ODL-SD document is invalid: {'; '.join(errors)}"
        )

    new_project = Project(
        name=request.project_name,
        description=request.description,
        owner_id=first_user.id,
        domain=request.domain,
        scale=request.scale,
        location_name=request.location,
        total_capacity_kw=str(request.capacity_kw) if request.capacity_kw else None,
        odl_document=json.dumps(odl_doc.to_dict(), indent=2),
        document_hash=odl_doc.meta.versioning.content_hash
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
        content_hash=new_project.document_hash[:8] if new_project.document_hash else "no-hash",
        is_active=True,
        created_at=new_project.created_at.isoformat() + "Z",
        updated_at=new_project.updated_at.isoformat() + "Z"
    )

@app.get("/documents/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get full ODL-SD document"""
    project = db.query(Project).filter(Project.id == document_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Document not found")

    if not project.odl_document:
        raise HTTPException(status_code=404, detail="ODL-SD document not generated for this project")

    try:
        odl_doc_dict = json.loads(project.odl_document)
        return odl_doc_dict
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid ODL-SD document format")

@app.post("/documents/{document_id}/validate", response_model=DocumentValidationResponse)
async def validate_document(document_id: str, db: Session = Depends(get_db)):
    """Validate ODL-SD document against schema"""
    project = db.query(Project).filter(Project.id == document_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Document not found")

    if not project.odl_document:
        raise HTTPException(status_code=404, detail="ODL-SD document not found")

    try:
        odl_doc_dict = json.loads(project.odl_document)
        odl_doc = OdlSdDocument(**odl_doc_dict)
        is_valid, errors = odl_doc.validate_document()

        return DocumentValidationResponse(
            is_valid=is_valid,
            errors=errors,
            document_hash=odl_doc.meta.versioning.content_hash,
            schema_version=odl_doc.schema_version
        )
    except Exception as e:
        return DocumentValidationResponse(
            is_valid=False,
            errors=[f"Document parsing error: {str(e)}"],
            document_hash="unknown",
            schema_version="unknown"
        )

@app.get("/documents/{document_id}/export")
async def export_document(document_id: str, format: str = "json", db: Session = Depends(get_db)):
    """Export ODL-SD document in various formats"""
    project = db.query(Project).filter(Project.id == document_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Document not found")

    if not project.odl_document:
        raise HTTPException(status_code=404, detail="ODL-SD document not found")

    if format.lower() not in ["json", "yaml"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'yaml'")

    try:
        odl_doc_dict = json.loads(project.odl_document)

        if format.lower() == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=odl_doc_dict,
                headers={"Content-Disposition": f"attachment; filename={project.name.replace(' ', '_')}_odl.json"}
            )
        elif format.lower() == "yaml":
            import yaml
            yaml_content = yaml.dump(odl_doc_dict, default_flow_style=False)
            from fastapi.responses import Response
            return Response(
                content=yaml_content,
                media_type="application/x-yaml",
                headers={"Content-Disposition": f"attachment; filename={project.name.replace(' ', '_')}_odl.yaml"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

if __name__ == "__main__":
    print("Starting OriginFD API with ODL-SD Document Generation...")
    print("Available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Features:")
    print("  - JWT Authentication")
    print("  - SQLite Database with ODL-SD storage")
    print("  - ODL-SD v4.1 document generation")
    print("  - Schema validation")
    print("  - Document versioning")
    print("  - Export (JSON/YAML)")
    print("Demo credentials: admin@originfd.com / admin")

    uvicorn.run(
        "odl_sd_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )