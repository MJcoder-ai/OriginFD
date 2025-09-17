"""Project model and schemas."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ProjectDomain(str, Enum):
    PV = "PV"
    BESS = "BESS"
    HYBRID = "HYBRID"


class ProjectScale(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    UTILITY = "utility"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"


class Project(Base):
    """Database model for projects."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    domain = Column(SqlEnum(ProjectDomain), nullable=False)
    scale = Column(SqlEnum(ProjectScale), nullable=False)
    status = Column(
        SqlEnum(ProjectStatus),
        default=ProjectStatus.DRAFT,
        nullable=False,
    )
    display_status = Column(String, default="draft")
    completion_percentage = Column(Integer, default=0)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country_code = Column(String(3), nullable=True)
    total_capacity_kw = Column(Float, nullable=True)
    tags = Column(String, default="[]")  # JSON string for SQLite compatibility
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    owner = relationship("User", back_populates="projects")
    is_archived = Column(Boolean, default=False)
    initialization_task_id = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def can_edit(self, user_id: str) -> bool:
        """Check if a user can edit this project."""
        return str(self.owner_id) == user_id

    def can_view(self, user_id: str) -> bool:
        """Check if a user can view this project."""
        # For now, only owner can view - expand this for team permissions later
        return str(self.owner_id) == user_id

    @property
    def tags_list(self) -> List[str]:
        """Get tags as a list from JSON string."""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []

    @tags_list.setter
    def tags_list(self, value: List[str]):
        """Set tags as JSON string from list."""
        self.tags = json.dumps(value) if value else "[]"


class ProjectSchema(BaseModel):
    """Pydantic schema for project responses."""

    id: uuid.UUID
    name: str
    description: Optional[str]
    domain: ProjectDomain
    scale: ProjectScale
    status: ProjectStatus
    display_status: str
    completion_percentage: int
    location_name: Optional[str]
    total_capacity_kw: Optional[float]
    tags: List[str]
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    initialization_task_id: Optional[str] = None

    class Config:
        from_attributes = True
