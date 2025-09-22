"""SQLAlchemy models for OriginFD API."""

# Import base classes and mixins first
from .base import Base, TenantMixin, TimestampMixin, UUIDMixin

# Models that depend on core models
from .component import Component

# Complex models with multiple dependencies last
from .document import Document
from .inventory_record import InventoryRecord
from .lifecycle import LifecycleGate, LifecycleGateApproval, LifecyclePhase
from .project import Project
from .supplier import Supplier

# Import models in dependency order to avoid circular imports
# Core models without foreign key dependencies first
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
    "LifecyclePhase",
    "LifecycleGate",
    "Component",
    "Supplier",
    "InventoryRecord",
    "Document",
    "LifecyclePhase",
    "LifecycleGate",
    "LifecycleGateApproval",
]
