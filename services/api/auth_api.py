#!/usr/bin/env python3
"""
Enhanced OriginFD API with JWT Authentication
"""
import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from core.auth import (
    authenticate_user, create_token_pair, verify_token,
    get_user_by_id, ACCESS_TOKEN_EXPIRE_MINUTES
)
from core.dependencies import CurrentUser, AdminUser, EngineerUser

# FastAPI app
app = FastAPI(
    title="OriginFD API",
    description="Enhanced API with JWT Authentication",
    version="0.2.0"
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


class RefreshRequest(BaseModel):
    refresh_token: str


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


# Basic endpoints
@app.get("/")
async def root():
    return {
        "name": "OriginFD API",
        "version": "0.2.0",
        "status": "running",
        "features": ["JWT Authentication", "Role-based Access Control"]
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected", "auth": "enabled"}


# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """Login with email and password"""
    user = authenticate_user(login_request.email, login_request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token data
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "roles": user["roles"]
    }
    
    # Create token pair
    access_token, refresh_token = create_token_pair(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request: RefreshRequest):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_token(refresh_request.refresh_token, token_type="refresh")
        
        user_id = payload.get("sub")
        user = get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new token data
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "roles": user["roles"]
        }
        
        # Create new token pair
        access_token, new_refresh_token = create_token_pair(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        is_active=current_user["is_active"],
        roles=current_user["roles"]
    )


@app.post("/auth/logout")
async def logout(current_user: CurrentUser):
    """Logout current user"""
    # In a real implementation, you'd invalidate the token
    # For now, just return success
    return {"message": "Successfully logged out"}


# Project endpoints (require authentication)
@app.get("/projects")
async def list_projects(current_user: CurrentUser):
    """List user's projects"""
    # Mock project data - in real app, filter by user
    projects = [
        {
            "id": "proj-1",
            "project_name": "Solar Farm Arizona Phase 1", 
            "domain": "PV",
            "scale": "UTILITY",
            "current_version": 3,
            "content_hash": "abc123",
            "is_active": True,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T14:30:00Z"
        },
        {
            "id": "proj-2", 
            "project_name": "Commercial BESS Installation",
            "domain": "BESS",
            "scale": "COMMERCIAL", 
            "current_version": 1,
            "content_hash": "def456",
            "is_active": True,
            "created_at": "2024-01-18T14:30:00Z",
            "updated_at": "2024-01-18T14:30:00Z"
        },
        {
            "id": "proj-3",
            "project_name": "Hybrid Microgrid Campus",
            "domain": "HYBRID", 
            "scale": "INDUSTRIAL",
            "current_version": 2,
            "content_hash": "ghi789",
            "is_active": True,
            "created_at": "2024-01-22T09:15:00Z",
            "updated_at": "2024-01-23T11:45:00Z"
        }
    ]
    
    return {"projects": projects}


@app.get("/projects/{project_id}")
async def get_project(project_id: str, current_user: CurrentUser):
    """Get specific project"""
    # Mock response - in real app, check user access
    return {
        "id": project_id,
        "project_name": "Solar Farm Arizona Phase 1",
        "domain": "PV",
        "scale": "UTILITY",
        "current_version": 3,
        "content_hash": "abc123",
        "is_active": True,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-20T14:30:00Z"
    }


@app.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreateRequest, 
    current_user: EngineerUser
):
    """Create new project (requires engineer role)"""
    import uuid
    
    return ProjectResponse(
        id=str(uuid.uuid4()),
        project_name=project_data.project_name,
        description=project_data.description,
        domain=project_data.domain,
        scale=project_data.scale,
        current_version=1,
        content_hash="new123",
        is_active=True,
        created_at=datetime.utcnow().isoformat() + "Z",
        updated_at=datetime.utcnow().isoformat() + "Z"
    )


@app.get("/documents/{document_id}")
async def get_document(document_id: str, current_user: CurrentUser):
    """Get ODL-SD document"""
    # Mock ODL-SD document
    return {
        "meta": {
            "project": "Solar Farm Arizona Phase 1",
            "domain": "PV",
            "scale": "UTILITY",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T14:30:00Z",
            "version": "v3"
        },
        "content": {
            "description": "Large-scale solar PV installation in Arizona",
            "capacity": "500 MW",
            "location": "Arizona, USA"
        }
    }


# Admin endpoints
@app.get("/admin/users")
async def list_users(admin_user: AdminUser):
    """List all users (admin only)"""
    from core.auth import MOCK_USERS_DB
    
    users = []
    for user_data in MOCK_USERS_DB.values():
        users.append({
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data.get("full_name"),
            "is_active": user_data["is_active"],
            "roles": user_data["roles"]
        })
    
    return {"users": users}


@app.get("/admin/stats")
async def get_admin_stats(admin_user: AdminUser):
    """Get admin statistics"""
    return {
        "total_users": 2,
        "active_users": 2,
        "total_projects": 3,
        "active_projects": 3,
        "system_status": "healthy"
    }


if __name__ == "__main__":
    print("Starting OriginFD API with JWT Authentication...")
    print("Available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Demo credentials:")
    print("  Admin: admin@originfd.com / admin")
    print("  User:  user@originfd.com / password")
    
    uvicorn.run(
        "auth_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )