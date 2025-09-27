"""
Tenant model for multi-tenant architecture.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class TenantMembership(Base, UUIDMixin, TimestampMixin):
    """Association table linking users to tenants with role metadata."""

    __tablename__ = "tenant_memberships"

    __table_args__ = {"extend_existing": True}
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    role = Column(String(50), nullable=False, default="member")
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)

    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="tenant_memberships")


class Tenant(Base, UUIDMixin, TimestampMixin):
    """
    Tenant model for multi-tenant row-level security.
    """

    __tablename__ = "tenants"

    __table_args__ = {"extend_existing": True}
    # Tenant Identity
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Settings
    settings = Column(Text)  # JSON settings

    # Subscription info (simplified for now)
    plan = Column(String(50), default="free")
    max_users = Column(String(10), default="5")
    max_projects = Column(String(10), default="10")

    memberships = relationship(
        "TenantMembership",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"
