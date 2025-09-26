"""
Authentication and authorization endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from core.config import get_settings
from core.database import SessionDep
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel, EmailStr

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    roles: list[str]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    # Use hardcoded secret for development
    secret_key = "B8rgVORF0jqDwtLesImXrbQmoBv+enPRRD8FGCfnOnIJ1SGZyZpDtnATLjF3C3zC7IKm5IAMeTwvMLFloIN5WQ=="
    return jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    # Use hardcoded secret for development
    secret_key = "B8rgVORF0jqDwtLesImXrbQmoBv+enPRRD8FGCfnOnIJ1SGZyZpDtnATLjF3C3zC7IKm5IAMeTwvMLFloIN5WQ=="
    return jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify JWT token."""
    settings = get_settings()
    try:
        # Use hardcoded secret for development
        secret_key = "B8rgVORF0jqDwtLesImXrbQmoBv+enPRRD8FGCfnOnIJ1SGZyZpDtnATLjF3C3zC7IKm5IAMeTwvMLFloIN5WQ=="
        payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Get user from database
    # user = db.query(User).filter(User.id == user_id).first()
    # if user is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="User not found"
    #     )

    # Mock user for now
    return {
        "id": user_id,
        "email": payload.get("email", "user@example.com"),
        "roles": payload.get("roles", ["user"]),
        "is_active": True,
    }


@router.post("/test")
async def test_login():
    """Test endpoint to verify auth router works."""
    return {"message": "Auth router is working"}


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """
    Authenticate user and return JWT tokens.
    """
    # Temporary mock authentication for demo - skip database query for now
    # TODO: Fix SQLAlchemy relationship issue between Project and primary_document
    if login_request.email not in ["admin@originfd.com", "user@originfd.com"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if login_request.password not in ["admin", "password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mock user data for demo
    user_data = {
        "sub": "mock-user-id",
        "email": login_request.email,
        "roles": ["admin"] if login_request.email == "admin@originfd.com" else ["user"],
    }

    settings = get_settings()
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token({"sub": user_data["sub"]})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    db: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Refresh access token using refresh token.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # TODO: Get user from database and verify they're still active
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user or not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="User not found or inactive"
    #     )

    # Mock user data for now
    user_data = {
        "sub": user_id,
        "email": "admin@originfd.com",
        "roles": ["admin", "engineer"],
    }

    settings = get_settings()
    access_token = create_access_token(user_data)
    new_refresh_token = create_refresh_token({"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=f"User {current_user['id']}",  # TODO: Get from database
        is_active=current_user["is_active"],
        roles=current_user["roles"],
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (in a real implementation, you'd invalidate the token).
    """
    # TODO: Add token to blacklist or invalidate in Redis
    return {"message": "Successfully logged out"}
