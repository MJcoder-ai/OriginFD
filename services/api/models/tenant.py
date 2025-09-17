"""
Tenant model for multi-tenant architecture.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class Tenant(Base, UUIDMixin, TimestampMixin):
    """
    Tenant model for multi-tenant row-level security.
    """

    __tablename__ = "tenants"

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

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"
