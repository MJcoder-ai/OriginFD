"""SQLAlchemy models for OriginFD API."""

if "_MODELS_INITIALIZED" in globals():
    # Module already initialized; reuse existing symbols
    pass
else:
    _MODELS_INITIALIZED = True

    # Import base classes and mixins first
    from .base import Base, TenantMixin, TimestampMixin, UUIDMixin
    from .lifecycle import (
        ApprovalDecision,
        GateStatus,
        LifecycleGate,
        LifecycleGateApproval,
        LifecyclePhase,
    )

    # Project and lifecycle domain models
    from .project import Project, ProjectDomain, ProjectScale, ProjectStatus
    from .document import Document, DocumentVersion

    # Core identity models
    from .tenant import Tenant, TenantMembership
    from .user import User

    __all__ = [
        "Base",
        "UUIDMixin",
        "TimestampMixin",
        "TenantMixin",
        "Tenant",
        "TenantMembership",
        "User",
        "Project",
        "ProjectDomain",
        "ProjectScale",
        "ProjectStatus",
        "Document",
        "DocumentVersion",
        "LifecyclePhase",
        "LifecycleGate",
        "LifecycleGateApproval",
        "GateStatus",
        "ApprovalDecision",
    ]
import sys as _sys

_ALIAS_TARGETS = {
    "models": __name__,
    "models.project": "services.api.models.project",
    "models.lifecycle": "services.api.models.lifecycle",
    "models.tenant": "services.api.models.tenant",
    "models.user": "services.api.models.user",
    "models.document": "services.api.models.document",
}
for alias, target in _ALIAS_TARGETS.items():
    module = _sys.modules.get(target)
    if module is not None:
        _sys.modules.setdefault(alias, module)
