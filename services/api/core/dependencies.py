"""
FastAPI dependency functions for authentication
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .auth import verify_token
from .database import get_db
from models.user import User

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)]
) -> dict:
    """
    Dependency to get current user from JWT token
    """
    token = credentials.credentials
    
    # Verify the token
    payload = verify_token(token, token_type="access")
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Convert to dict for compatibility
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": user.roles
    }


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user_from_token)]
) -> dict:
    """
    Dependency to get current active user
    """
    return current_user


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific roles
    Usage: Depends(require_roles("admin", "engineer"))
    """
    def role_checker(current_user: Annotated[dict, Depends(get_current_active_user)]) -> dict:
        user_roles = current_user.get("roles", [])
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


# Common dependency aliases for convenience
CurrentUser = Annotated[dict, Depends(get_current_active_user)]
AdminUser = Annotated[dict, Depends(require_roles("admin"))]
EngineerUser = Annotated[dict, Depends(require_roles("admin", "engineer"))]