"""Shared FastAPI dependency utilities for authentication."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any, Dict, List

import models
from core.auth import verify_token
from core.database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)


def _normalize_roles(user: models.User, payload: Dict[str, Any]) -> List[str]:
    """Extract role information from the JWT payload or user record."""

    roles: List[str] = []

    payload_roles = payload.get("roles")
    if isinstance(payload_roles, list):
        roles = [str(role) for role in payload_roles if role]

    if not roles:
        user_roles = getattr(user, "roles", None)
        if isinstance(user_roles, list):
            roles = [str(role) for role in user_roles if role]
        elif user_roles:
            roles = [str(user_roles)]

    if not roles:
        fallback_role = getattr(user, "role", None)
        if fallback_role:
            roles = [str(fallback_role)]

    if not roles:
        roles = ["user"]

    return roles


def _serialize_membership(membership: models.TenantMembership) -> Dict[str, Any]:
    tenant = membership.tenant
    return {
        "tenant_id": str(membership.tenant_id),
        "tenant_name": getattr(tenant, "name", None),
        "tenant_slug": getattr(tenant, "slug", None),
        "role": membership.role,
        "is_default": bool(membership.is_default),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Resolve the currently authenticated user including tenant bindings."""

    token = (credentials.credentials or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token, token_type="access")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(user_id))
    except (TypeError, ValueError) as exc:
        logger.debug("Invalid user identifier in token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user: models.User | None = (
        db.query(models.User)
        .options(joinedload(models.User.tenant_memberships).joinedload(models.TenantMembership.tenant))
        .filter(models.User.id == user_uuid)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if hasattr(user, "is_active") and not bool(user.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    active_memberships = [
        m
        for m in getattr(user, "tenant_memberships", [])
        if bool(m.is_active) and (m.tenant is None or bool(getattr(m.tenant, "is_active", True)))
    ]

    if not active_memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not bound to an active tenant",
        )

    default_membership = next(
        (membership for membership in active_memberships if bool(membership.is_default)),
        active_memberships[0],
    )

    memberships_payload = [_serialize_membership(m) for m in active_memberships]
    for membership in memberships_payload:
        membership["is_default"] = membership["tenant_id"] == str(default_membership.tenant_id)

    user_roles = _normalize_roles(user, payload)

    current_user = {
        "id": str(user.id),
        "email": getattr(user, "email", None),
        "full_name": getattr(user, "full_name", None),
        "is_active": bool(getattr(user, "is_active", True)),
        "roles": user_roles,
        "tenant_id": str(default_membership.tenant_id),
        "tenant_slug": getattr(default_membership.tenant, "slug", None),
        "tenants": memberships_payload,
    }

    return current_user


CurrentUser = Annotated[Dict[str, Any], Depends(get_current_user)]
