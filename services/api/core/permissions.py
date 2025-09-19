"""
Production-grade Role-Based Access Control (RBAC) system.
Implements comprehensive authorization checks for all resources.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from api.routers.auth import get_current_user
from core.database import get_db
from fastapi import Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# =====================================
# Permission System Enums
# =====================================


class Permission(str, Enum):
    """Granular permissions for resources and actions."""

    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_SHARE = "project:share"
    PROJECT_EXPORT = "project:export"

    # Component permissions
    COMPONENT_CREATE = "component:create"
    COMPONENT_READ = "component:read"
    COMPONENT_UPDATE = "component:update"
    COMPONENT_DELETE = "component:delete"
    COMPONENT_APPROVE = "component:approve"
    COMPONENT_TRANSITION = "component:transition"

    # Document permissions
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_VERSION = "document:version"

    # User management permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_INVITE = "user:invite"

    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_CONFIG = "system:config"

    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"


class Role(str, Enum):
    """User roles with hierarchical permissions."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
    GUEST = "guest"


class ResourceType(str, Enum):
    """Types of resources that can be protected."""

    PROJECT = "project"
    COMPONENT = "component"
    DOCUMENT = "document"
    USER = "user"
    SYSTEM = "system"


# =====================================
# Role-Permission Mapping
# =====================================

ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.SUPER_ADMIN: [
        # Full system access
        Permission.SYSTEM_ADMIN,
        Permission.SYSTEM_MONITOR,
        Permission.SYSTEM_CONFIG,
        # Full user management
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_INVITE,
        # Full project access
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_SHARE,
        Permission.PROJECT_EXPORT,
        # Full component access
        Permission.COMPONENT_CREATE,
        Permission.COMPONENT_READ,
        Permission.COMPONENT_UPDATE,
        Permission.COMPONENT_DELETE,
        Permission.COMPONENT_APPROVE,
        Permission.COMPONENT_TRANSITION,
        # Full document access
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_VERSION,
        # Analytics access
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_EXPORT,
    ],
    Role.ADMIN: [
        # Limited system access
        Permission.SYSTEM_MONITOR,
        # User management (excluding create/delete)
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_INVITE,
        # Full project access
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_SHARE,
        Permission.PROJECT_EXPORT,
        # Full component access
        Permission.COMPONENT_CREATE,
        Permission.COMPONENT_READ,
        Permission.COMPONENT_UPDATE,
        Permission.COMPONENT_DELETE,
        Permission.COMPONENT_APPROVE,
        Permission.COMPONENT_TRANSITION,
        # Full document access
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_VERSION,
        # Analytics access
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_EXPORT,
    ],
    Role.ENGINEER: [
        # Basic user access
        Permission.USER_READ,
        # Project management
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_SHARE,
        Permission.PROJECT_EXPORT,
        # Component management
        Permission.COMPONENT_CREATE,
        Permission.COMPONENT_READ,
        Permission.COMPONENT_UPDATE,
        Permission.COMPONENT_TRANSITION,
        # Document management
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_VERSION,
        # Analytics read access
        Permission.ANALYTICS_READ,
    ],
    Role.REVIEWER: [
        # Basic user access
        Permission.USER_READ,
        # Project read access
        Permission.PROJECT_READ,
        Permission.PROJECT_EXPORT,
        # Component review access
        Permission.COMPONENT_READ,
        Permission.COMPONENT_APPROVE,
        Permission.COMPONENT_TRANSITION,
        # Document read/version access
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_VERSION,
        # Analytics read access
        Permission.ANALYTICS_READ,
    ],
    Role.VIEWER: [
        # Basic user access
        Permission.USER_READ,
        # Read-only project access
        Permission.PROJECT_READ,
        # Read-only component access
        Permission.COMPONENT_READ,
        # Read-only document access
        Permission.DOCUMENT_READ,
        # Read-only analytics access
        Permission.ANALYTICS_READ,
    ],
    Role.GUEST: [
        # Very limited read access
        Permission.PROJECT_READ,
        Permission.COMPONENT_READ,
        Permission.DOCUMENT_READ,
    ],
}

# =====================================
# Authorization Classes
# =====================================


class AuthorizationError(HTTPException):
    """Custom authorization error with detailed messaging."""

    def __init__(
        self, message: str = "Access denied", resource: str = None, action: str = None
    ):
        detail = message
        if resource and action:
            detail = (
                f"Access denied: insufficient permissions for {action} on {resource}"
            )

        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class AuthorizationContext:
    """Context for authorization decisions."""

    def __init__(
        self,
        user: Dict[str, Any],
        resource_type: ResourceType,
        resource_id: Optional[Union[str, UUID]] = None,
        action: Optional[Permission] = None,
        resource_data: Optional[Dict[str, Any]] = None,
    ):
        self.user = user
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.resource_data = resource_data


class PermissionChecker:
    """Centralized permission checking logic."""

    def __init__(self, db: Session):
        self.db = db

    def user_has_permission(self, user: Dict[str, Any], permission: Permission) -> bool:
        """Check if user has a specific permission based on their role."""
        user_role = Role(user.get("role", Role.GUEST))
        role_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return permission in role_permissions

    def user_has_any_permission(
        self, user: Dict[str, Any], permissions: List[Permission]
    ) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.user_has_permission(user, perm) for perm in permissions)

    def user_has_all_permissions(
        self, user: Dict[str, Any], permissions: List[Permission]
    ) -> bool:
        """Check if user has all of the specified permissions."""
        return all(self.user_has_permission(user, perm) for perm in permissions)

    def check_resource_ownership(
        self,
        user: Dict[str, Any],
        resource_type: ResourceType,
        resource_id: Union[str, UUID],
        require_ownership: bool = True,
    ) -> Optional[Any]:
        """Check if user owns or has access to a resource."""

        try:
            resource_id_uuid = UUID(str(resource_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resource ID format",
            )

        user_id = UUID(user["id"])
        tenant_id = UUID(user["tenant_id"])

        if resource_type == ResourceType.PROJECT:
            import models

            query = self.db.query(models.Project).filter(
                and_(
                    models.Project.id == resource_id_uuid,
                    models.Project.tenant_id == tenant_id,
                )
            )

            if require_ownership:
                query = query.filter(models.Project.owner_id == user_id)

            resource = query.first()

        elif resource_type == ResourceType.COMPONENT:
            import models

            query = self.db.query(models.Component).filter(
                and_(
                    models.Component.id == resource_id_uuid,
                    models.Component.tenant_id == tenant_id,
                )
            )

            if require_ownership:
                query = query.filter(models.Component.created_by == user_id)

            resource = query.first()

        elif resource_type == ResourceType.DOCUMENT:
            import models

            query = self.db.query(models.Document).filter(
                and_(
                    models.Document.id == resource_id_uuid,
                    models.Document.tenant_id == tenant_id,
                )
            )

            if require_ownership:
                query = query.filter(models.Document.created_by == user_id)

            resource = query.first()

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported resource type: {resource_type}",
            )

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type.value.title()} not found",
            )

        return resource

    def authorize(self, context: AuthorizationContext) -> Any:
        """Main authorization check with comprehensive logic."""

        # Check basic permission
        if context.action and not self.user_has_permission(
            context.user, context.action
        ):
            # Special case: allow users to read their own resources
            if context.action in [
                Permission.PROJECT_READ,
                Permission.COMPONENT_READ,
                Permission.DOCUMENT_READ,
            ]:
                if context.resource_id:
                    try:
                        resource = self.check_resource_ownership(
                            context.user,
                            context.resource_type,
                            context.resource_id,
                            require_ownership=True,
                        )
                        return resource
                    except HTTPException:
                        pass  # Fall through to authorization error

            raise AuthorizationError(
                f"Insufficient permissions for {context.action}",
                context.resource_type.value,
                context.action.value,
            )

        # Check resource-specific access
        if context.resource_id:
            # Determine if ownership is required based on user role and action
            user_role = Role(context.user.get("role", Role.GUEST))
            require_ownership = user_role not in [
                Role.SUPER_ADMIN,
                Role.ADMIN,
            ] and context.action not in [
                Permission.COMPONENT_APPROVE,
                Permission.PROJECT_READ,
            ]

            resource = self.check_resource_ownership(
                context.user,
                context.resource_type,
                context.resource_id,
                require_ownership=require_ownership,
            )
            return resource

        return True


# =====================================
# FastAPI Dependencies
# =====================================


def get_permission_checker(db: Session = Depends(get_db)) -> PermissionChecker:
    """Get permission checker instance."""
    return PermissionChecker(db)


def require_permission(permission: Permission):
    """Dependency factory for requiring specific permissions."""

    def check_permission(
        user: Dict[str, Any] = Depends(get_current_user),
        checker: PermissionChecker = Depends(get_permission_checker),
    ):
        if not checker.user_has_permission(user, permission):
            raise AuthorizationError(
                f"Required permission: {permission}", action=permission.value
            )
        return user

    return check_permission


def require_any_permission(permissions: List[Permission]):
    """Dependency factory for requiring any of the specified permissions."""

    def check_permissions(
        user: Dict[str, Any] = Depends(get_current_user),
        checker: PermissionChecker = Depends(get_permission_checker),
    ):
        if not checker.user_has_any_permission(user, permissions):
            perm_names = [p.value for p in permissions]
            raise AuthorizationError(
                f"Required any of: {', '.join(perm_names)}", action="multiple"
            )
        return user

    return check_permissions


def require_resource_access(
    resource_type: ResourceType, permission: Permission, require_ownership: bool = True
):
    """Dependency factory for resource-specific access control."""

    def check_access(
        resource_id: UUID,
        user: Dict[str, Any] = Depends(get_current_user),
        checker: PermissionChecker = Depends(get_permission_checker),
    ):
        context = AuthorizationContext(
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            action=permission,
        )

        return checker.authorize(context)

    return check_access


# =====================================
# Convenience Dependencies
# =====================================


# Project access dependencies
def get_project_for_user(
    project_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker),
):
    """Get project with read access verification."""
    context = AuthorizationContext(
        user=user,
        resource_type=ResourceType.PROJECT,
        resource_id=project_id,
        action=Permission.PROJECT_READ,
    )
    return checker.authorize(context)


def get_project_for_update(
    project_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker),
):
    """Get project with update access verification."""
    context = AuthorizationContext(
        user=user,
        resource_type=ResourceType.PROJECT,
        resource_id=project_id,
        action=Permission.PROJECT_UPDATE,
    )
    return checker.authorize(context)


# Component access dependencies
def get_component_for_user(
    component_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker),
):
    """Get component with read access verification."""
    context = AuthorizationContext(
        user=user,
        resource_type=ResourceType.COMPONENT,
        resource_id=component_id,
        action=Permission.COMPONENT_READ,
    )
    return checker.authorize(context)


def get_component_for_update(
    component_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker),
):
    """Get component with update access verification."""
    context = AuthorizationContext(
        user=user,
        resource_type=ResourceType.COMPONENT,
        resource_id=component_id,
        action=Permission.COMPONENT_UPDATE,
    )
    return checker.authorize(context)


# Document access dependencies
def get_document_for_user(
    document_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user),
    checker: PermissionChecker = Depends(get_permission_checker),
):
    """Get document with read access verification."""
    context = AuthorizationContext(
        user=user,
        resource_type=ResourceType.DOCUMENT,
        resource_id=document_id,
        action=Permission.DOCUMENT_READ,
    )
    return checker.authorize(context)


# =====================================
# Utility Functions
# =====================================


def get_user_permissions(user: Dict[str, Any]) -> List[Permission]:
    """Get all permissions for a user based on their role."""
    user_role = Role(user.get("role", Role.GUEST))
    return ROLE_PERMISSIONS.get(user_role, [])


def can_user_access_resource(
    user: Dict[str, Any], resource_type: ResourceType, action: Permission, db: Session
) -> bool:
    """Check if user can perform action on resource type."""
    checker = PermissionChecker(db)
    return checker.user_has_permission(user, action)


def filter_resources_for_user(
    user: Dict[str, Any], resource_type: ResourceType, db: Session
):
    """Get query filter for resources accessible to user."""
    user_id = UUID(user["id"])
    tenant_id = UUID(user["tenant_id"])
    user_role = Role(user.get("role", Role.GUEST))

    # Super admins and admins can see all resources in their tenant
    if user_role in [Role.SUPER_ADMIN, Role.ADMIN]:
        return {"tenant_id": tenant_id}

    # Others can only see their own resources
    if resource_type == ResourceType.PROJECT:
        return {"tenant_id": tenant_id, "owner_id": user_id}
    elif resource_type == ResourceType.COMPONENT:
        return {"tenant_id": tenant_id, "created_by": user_id}
    elif resource_type == ResourceType.DOCUMENT:
        return {"tenant_id": tenant_id, "created_by": user_id}

    return {"tenant_id": tenant_id}
