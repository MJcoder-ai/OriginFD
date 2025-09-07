#!/usr/bin/env python3
"""
Simple test script for OriginFD API endpoints.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Simple test app without complex configuration
app = FastAPI(
    title="OriginFD API Test",
    description="Test API for OriginFD Backend",
    version="0.1.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models for testing
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    roles: list[str] = ["user"]

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    domain: str
    scale: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    domain: str
    scale: str
    status: str
    created_at: str

# Test endpoints
@app.get("/")
async def root():
    return {
        "name": "OriginFD API Test",
        "version": "0.1.0",
        "status": "running",
        "endpoints": ["/auth/login", "/auth/me", "/projects"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """Test login endpoint with demo credentials."""
    if login_request.email == "admin@originfd.com" and login_request.password == "admin":
        return TokenResponse(
            access_token="demo-access-token-12345",
            refresh_token="demo-refresh-token-67890",
            expires_in=1800
        )
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@app.get("/auth/me", response_model=UserResponse)  
async def get_current_user():
    """Test current user endpoint."""
    return UserResponse(
        id="demo-user-123",
        email="admin@originfd.com",
        full_name="Admin User",
        roles=["admin", "engineer"]
    )

@app.get("/projects")
async def list_projects():
    """Test projects list endpoint."""
    return {
        "projects": [
            {
                "id": "proj-1",
                "name": "Solar Farm Arizona Phase 1", 
                "domain": "PV",
                "scale": "UTILITY",
                "status": "ACTIVE",
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": "proj-2", 
                "name": "Commercial BESS Installation",
                "domain": "BESS",
                "scale": "COMMERCIAL", 
                "status": "DRAFT",
                "created_at": "2024-01-18T14:30:00Z"
            },
            {
                "id": "proj-3",
                "name": "Hybrid Microgrid Campus",
                "domain": "HYBRID", 
                "scale": "INDUSTRIAL",
                "status": "UNDER_REVIEW",
                "created_at": "2024-01-22T09:15:00Z"
            }
        ],
        "total": 3,
        "page": 1,
        "page_size": 20
    }

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreateRequest):
    """Test project creation endpoint."""
    import uuid
    from datetime import datetime
    
    return ProjectResponse(
        id=str(uuid.uuid4()),
        name=project_data.name,
        description=project_data.description,
        domain=project_data.domain,
        scale=project_data.scale,
        status="DRAFT",
        created_at=datetime.utcnow().isoformat() + "Z"
    )

@app.get("/projects/stats/summary") 
async def get_project_stats():
    """Test project statistics endpoint."""
    return {
        "total_projects": 3,
        "active_projects": 1,
        "pv_projects": 1, 
        "bess_projects": 1,
        "hybrid_projects": 1
    }

if __name__ == "__main__":
    print("Starting OriginFD API Test Server...")
    print("Available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Demo credentials: admin@originfd.com / admin")
    
    uvicorn.run(
        "test_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )