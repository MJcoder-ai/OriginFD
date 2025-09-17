"""Supplier model and schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Supplier(Base):
    """Represents a supplier or manufacturer."""

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
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
    components = relationship("Component", back_populates="supplier")


class SupplierSchema(BaseModel):
    id: uuid.UUID
    name: str
    contact_email: Optional[EmailStr] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
