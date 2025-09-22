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