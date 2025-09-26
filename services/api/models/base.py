"""
Base classes and mixins for SQLAlchemy models.
"""

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import text


class UUIDMixin:
    """Mixin that adds a UUID primary key."""

    __allow_unmapped__ = True

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp fields."""

    __allow_unmapped__ = True

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )


class TenantMixin:
    """Mixin that adds tenant_id for multi-tenant row-level security."""

    __allow_unmapped__ = True

    @declared_attr
    def tenant_id(cls):
        return Column(
            UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
        )


__all__ = ["Base", "UUIDMixin", "TimestampMixin", "TenantMixin"]
