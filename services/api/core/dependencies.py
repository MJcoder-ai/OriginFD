"""
FastAPI dependency functions for authentication and caching.
"""

import json
import logging
from functools import lru_cache
from typing import Annotated, Optional

import models
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .auth import verify_token
from .config import settings
from .database import get_db

# HTTP Bearer token scheme
security = HTTPBearer()
logger = logging.getLogger(__name__)


async def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
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
            detail="Invalid token: missing user ID",
        )

    # Get user from database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Convert to dict for compatibility
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": user.roles,
    }


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user_from_token)],
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

    def role_checker(
        current_user: Annotated[dict, Depends(get_current_active_user)],
    ) -> dict:
        user_roles = current_user.get("roles", [])

        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )

        return current_user

    return role_checker


# Common dependency aliases for convenience
CurrentUser = Annotated[dict, Depends(get_current_active_user)]
AdminUser = Annotated[dict, Depends(require_roles("admin"))]
EngineerUser = Annotated[dict, Depends(require_roles("admin", "engineer"))]


# =====================================
# Redis Caching Dependencies
# =====================================


@lru_cache()
def get_redis_client() -> redis.Redis:
    """
    Get Redis client with connection pooling and proper configuration.
    Uses LRU cache to ensure single instance per process.
    """
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Test connection
        redis_client.ping()
        return redis_client
    except Exception as exc:
        logger.warning("Redis connection unavailable, using mock client: %s", exc)
        # Fall back to mock implementation if Redis is unavailable
        from unittest.mock import MagicMock

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        return mock_redis


def get_cache_service(redis_client: redis.Redis = Depends(get_redis_client)):
    """
    Dependency to get cache service instance.
    """
    return CacheService(redis_client)


class CacheService:
    """
    Production-grade caching service with Redis backend.
    Provides type-safe caching operations with automatic serialization.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes default TTL

    def get_cached_data(self, key: str) -> Optional[dict]:
        """Get cached data with automatic deserialization."""
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except (json.JSONDecodeError, redis.RedisError) as exc:
            # Log error but don't fail - graceful degradation
            logger.debug("Failed to decode cached data for %s: %s", key, exc)
            return None

    def set_cached_data(self, key: str, data: dict, ttl: Optional[int] = None) -> bool:
        """Set cached data with automatic serialization."""
        try:
            ttl = ttl or self.default_ttl
            serialized_data = json.dumps(data, default=str)
            return self.redis.setex(key, ttl, serialized_data)
        except (json.JSONEncodeError, redis.RedisError) as exc:
            # Log error but don't fail - graceful degradation
            logger.debug("Failed to cache %s: %s", key, exc)
            return False

    def delete_cached_data(self, key: str) -> bool:
        """Delete cached data."""
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError:
            return False

    def get_cached_component(self, component_id: int) -> Optional[dict]:
        """Get cached component data."""
        return self.get_cached_data(f"component:{component_id}")

    def cache_component(
        self, component_id: int, component_data: dict, ttl: int = 600
    ) -> bool:
        """Cache component data with 10-minute TTL."""
        return self.set_cached_data(f"component:{component_id}", component_data, ttl)

    def get_cached_project(self, project_id: str) -> Optional[dict]:
        """Get cached project data."""
        return self.get_cached_data(f"project:{project_id}")

    def cache_project(
        self, project_id: str, project_data: dict, ttl: int = 300
    ) -> bool:
        """Cache project data with 5-minute TTL."""
        return self.set_cached_data(f"project:{project_id}", project_data, ttl)

    def invalidate_component_cache(self, component_id: int) -> bool:
        """Invalidate component cache when data changes."""
        return self.delete_cached_data(f"component:{component_id}")

    def invalidate_project_cache(self, project_id: str) -> bool:
        """Invalidate project cache when data changes."""
        return self.delete_cached_data(f"project:{project_id}")


# Cache service dependency alias
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
