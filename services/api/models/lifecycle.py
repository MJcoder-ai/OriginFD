"""Lifecycle phase, gate, and approval models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class GateStatus(str, Enum):
    """Lifecycle gate execution status."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalDecision(str, Enum):
    """Lifecycle gate approval decision."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"


class LifecyclePhase(Base, UUIDMixin, TimestampMixin):
    """Lifecycle phases associated with a project."""

    __tablename__ = "lifecycle_phases"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "phase_code", name="uq_lifecycle_phases_project_phase_code"
        ),
        {"extend_existing": True},
    )

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    phase_code = Column(Integer, nullable=False, index=True)
    phase_key = Column(String(length=128), nullable=False, index=True)
    title = Column(String(length=256), nullable=False)
    order = Column(Integer, nullable=False, index=True)
    entry_gate_code = Column(String(length=16), nullable=False)
    exit_gate_code = Column(String(length=16), nullable=False)
    required_entry_roles = Column(JSON, nullable=False, default=list)
    required_exit_roles = Column(JSON, nullable=False, default=list)
    odl_sd_sections = Column(JSON, nullable=False, default=list)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sequence = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False)
    context = Column(JSON, default=dict)

    project = relationship("Project", back_populates="lifecycle_phases")
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
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "phase_code",
            "gate_code",
            name="uq_lifecycle_gates_project_phase_gate",
        ),
        {"extend_existing": True},
    )

    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    phase_id = Column(
        UUID(as_uuid=True), ForeignKey("lifecycle_phases.id"), nullable=False
    )
    phase_code = Column(Integer, nullable=False, index=True)
    gate_code = Column(String(length=16), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sequence = Column(Integer, nullable=False)
    status = Column(
        SAEnum(GateStatus, name="gate_status"),
        default=GateStatus.NOT_STARTED.value,
        server_default=GateStatus.NOT_STARTED.value,
        nullable=False,
        index=True,
    )
    due_date = Column(DateTime(timezone=True), nullable=True)
    owner = Column(String, nullable=True)
    context = Column(JSON, default=dict, nullable=False)

    project = relationship("Project", back_populates="lifecycle_gates")
    phase = relationship("LifecyclePhase", back_populates="gates")
    approvals = relationship(
        "LifecycleGateApproval",
        back_populates="gate",
        cascade="all, delete-orphan",
        order_by="LifecycleGateApproval.created_at",
    )

    def context_dict(self) -> Dict[str, Any]:
        """Return metadata as a dictionary."""

        value = self.context or {}
        return value if isinstance(value, dict) else {}

    @property
    def approval(self) -> Optional["LifecycleGateApproval"]:
        """Maintain backward compatibility with legacy single-approval access."""

        if not self.approvals:
            return None
        return self.approvals[0]


class LifecycleGateApproval(Base, UUIDMixin, TimestampMixin):
    """Approval status for lifecycle gates."""

    __tablename__ = "lifecycle_gate_approvals"
    __table_args__ = {"extend_existing": True}

    gate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lifecycle_gates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approver_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    role_key = Column(String(length=128), nullable=False)
    decision = Column(
        SAEnum(ApprovalDecision, name="approval_decision"),
        nullable=False,
        default=ApprovalDecision.APPROVE.value,
        server_default=ApprovalDecision.APPROVE.value,
    )
    comment = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    comments = Column(String, nullable=True)

    gate = relationship("LifecycleGate", back_populates="approvals")

    def as_dict(self) -> Dict[str, Optional[str]]:
        """Serialize approval metadata for API responses."""

        effective_comment = self.comment if self.comment is not None else self.comments
        decided_by_value = self.decided_by or self.approver_user_id

        return {
            "status": self.status,
            "decided_by": str(decided_by_value) if decided_by_value else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "comments": effective_comment,
        }


__all__ = [
    "GateStatus",
    "ApprovalDecision",
    "LifecyclePhase",
    "LifecycleGate",
    "LifecycleGateApproval",
]
