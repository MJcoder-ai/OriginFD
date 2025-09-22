"""Lifecycle phase and gate models."""

from __future__ import annotations

from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class LifecyclePhase(Base, UUIDMixin, TimestampMixin):
    """Represents a workflow phase for a project."""

    __tablename__ = "lifecycle_phases"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="not_started")
    position = Column(Integer, nullable=False, default=0)

    project: "Project" = relationship("Project", back_populates="lifecycle_phases")
    lifecycle_gates: List["LifecycleGate"] = relationship(
        "LifecycleGate",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="LifecycleGate.position",
    )

    __table_args__ = (
        UniqueConstraint("project_id", "key", name="uq_lifecycle_phases_project_key"),
    )


class LifecycleGate(Base, UUIDMixin, TimestampMixin):
    """Represents a gate/checkpoint within a lifecycle phase."""

    __tablename__ = "lifecycle_gates"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lifecycle_phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="not_started")
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    position = Column(Integer, nullable=False, default=0)

    project: "Project" = relationship("Project", back_populates="lifecycle_gates")
    phase: LifecyclePhase = relationship("LifecyclePhase", back_populates="lifecycle_gates")

    __table_args__ = (
        UniqueConstraint("phase_id", "key", name="uq_lifecycle_gates_phase_key"),
    )


__all__ = ["LifecyclePhase", "LifecycleGate"]
