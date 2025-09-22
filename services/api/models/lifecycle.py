"""Lifecycle phase, gate, and approval models."""

from __future__ import annotations

from typing import List, Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, JSON, UniqueConstraint

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class LifecyclePhase(Base, UUIDMixin, TimestampMixin):

    """Lifecycle phases associated with a project."""

    __tablename__ = "lifecycle_phases"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sequence = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False)
    context = Column(JSON, default=dict)

    gates = relationship(
        "LifecycleGate",
        back_populates="phase",
        order_by="LifecycleGate.sequence",
        cascade="all, delete-orphan",
    )

    def context_dict(self) -> Dict[str, Any]:
        """Return metadata as a dictionary."""

        value = self.context or {}
        return value if isinstance(value, dict) else {}


class LifecycleGate(Base, UUIDMixin, TimestampMixin):
    """Individual lifecycle gates within a phase."""

    __tablename__ = "lifecycle_gates"

    phase_id = Column(UUID(as_uuid=True), ForeignKey("lifecycle_phases.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sequence = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    owner = Column(String, nullable=True)
    context = Column(JSON, default=dict)

    phase = relationship("LifecyclePhase", back_populates="gates")
    approval = relationship(
        "LifecycleGateApproval",
        back_populates="gate",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def context_dict(self) -> Dict[str, Any]:
        """Return metadata as a dictionary."""

        value = self.context or {}
        return value if isinstance(value, dict) else {}


class LifecycleGateApproval(Base, UUIDMixin, TimestampMixin):
    """Approval status for lifecycle gates."""

    __tablename__ = "lifecycle_gate_approvals"

    gate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lifecycle_gates.id"),
        nullable=False,
        unique=True,
    )
    status = Column(String, default="pending", nullable=False)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    comments = Column(String, nullable=True)

    gate = relationship("LifecycleGate", back_populates="approval")

    def as_dict(self) -> Dict[str, Optional[str]]:
        """Serialize approval metadata for API responses."""

        return {
            "status": self.status,
            "decided_by": str(self.decided_by) if self.decided_by else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "comments": self.comments,
        }


__all__ = ["LifecyclePhase", "LifecycleGate", "LifecycleGateApproval"]


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

