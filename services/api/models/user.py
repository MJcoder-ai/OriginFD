"""SQLAlchemy models and Pydantic schemas for users."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """Database model for application users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # Single role for SQLite compatibility
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    projects = relationship("Project", back_populates="owner")

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.updated_at = datetime.utcnow()


class UserSchema(BaseModel):
    """Pydantic schema for user information."""

    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False
    role: str = "user"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
