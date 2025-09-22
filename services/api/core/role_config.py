"""Centralized role-to-permission configuration for API services."""

from __future__ import annotations

from typing import Dict, List


# NOTE: Permissions are expressed using their string representation to avoid
# circular imports with ``core.permissions``. The ``Permission`` enum in that
# module should contain matching values for each string defined below.
ROLE_ACTION_MAP: Dict[str, List[str]] = {
    # Read-only consumers of project documentation.
    "viewer": [
        "document:read",
    ],
    # Engineers can both inspect and iterate on documentation updates.
    "engineer": [
        "document:read",
        "document:update",
        "document:version",
    ],
    # Project managers share similar capabilities to engineers but may also
    # coordinate version management activities.
    "project_manager": [
        "document:read",
        "document:update",
        "document:version",
    ],
    # Administrators retain full control of documentation lifecycle actions.
    "admin": [
        "document:create",
        "document:read",
        "document:update",
        "document:delete",
        "document:version",
    ],
}

