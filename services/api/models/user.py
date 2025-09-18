"""SQLAlchemy models and Pydantic schemas for users."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """Database model for application users."""

    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # Single role for SQLite compatibility

    # Relationships
    projects = relationship("Project", back_populates="owner")

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        # The updated_at field is automatically updated by SQLAlchemy onupdate
        # This method is for manual timestamp updates if needed
        pass


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
