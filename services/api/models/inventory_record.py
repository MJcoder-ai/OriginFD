"""Inventory record model and schema."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from .base import Base


class InventoryRecord(Base):
    """Tracks inventory for components."""

    __tablename__ = "inventory_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_id = Column(
        UUID(as_uuid=True), ForeignKey("components.id"), nullable=False
    )
    quantity = Column(Integer, default=0)
    location = Column(String, nullable=True)
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
    component = relationship("Component", back_populates="inventory_records")


class InventoryRecordSchema(BaseModel):
    id: uuid.UUID
    component_id: uuid.UUID
    quantity: int
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
