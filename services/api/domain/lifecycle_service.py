from __future__ import annotations

"""Domain services for lifecycle gate updates."""

from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.domain.lifecycle_hooks import emit_phase_milestone
from services.api.models.lifecycle import (
    ApprovalDecision,
    GateStatus,
    LifecycleGate,
    LifecycleGateApproval,
    LifecyclePhase,
)


class GateUpdateError(ValueError):
    """Raised when a lifecycle gate update cannot be performed."""


class ForbiddenApprovalError(PermissionError):
    """Raised when an approver does not have the required role access."""


def _which_gate(phase: LifecyclePhase, gate_code: str) -> str:
    if gate_code == phase.entry_gate_code:
        return "entry"
    if gate_code == phase.exit_gate_code:
        return "exit"
    raise GateUpdateError(
        f"Gate {gate_code} does not belong to phase_code={phase.phase_code}"
    )


def _required_roles(phase: LifecyclePhase, which: str) -> list[str]:
    roles = (
        phase.required_entry_roles if which == "entry" else phase.required_exit_roles
    )
    return list(roles or [])


def _derive_gate_name(phase: LifecyclePhase, which: str, gate_code: str) -> str:
    label = "Entry" if which == "entry" else "Exit"
    return f"{phase.title} {label} ({gate_code})"


def update_gate_status(
    session: Session,
    *,
    project_id,
    phase_code: int,
    gate_code: str,
    decision: ApprovalDecision,
    role_key: str,
    approver_user_id,
    comment: Optional[str] = None,
) -> Tuple[LifecycleGate, LifecycleGateApproval]:
    """Validate role access, persist gate status, and append approval history."""

    phase = session.execute(
        select(LifecyclePhase).where(
            LifecyclePhase.project_id == project_id,
            LifecyclePhase.phase_code == phase_code,
        )
    ).scalar_one_or_none()
    if phase is None:
        raise GateUpdateError(f"Phase {phase_code} not found for project {project_id}")

    which = _which_gate(phase, gate_code)
    allowed = _required_roles(phase, which)
    if allowed and role_key not in allowed:
        raise ForbiddenApprovalError(
            f"Role {role_key} not permitted for {which} of phase {phase_code}"
        )

    gate = session.execute(
        select(LifecycleGate).where(
            LifecycleGate.project_id == project_id,
            LifecycleGate.phase_code == phase_code,
            LifecycleGate.gate_code == gate_code,
        )
    ).scalar_one_or_none()

    new_status = (
        GateStatus.APPROVED
        if decision == ApprovalDecision.APPROVE
        else GateStatus.REJECTED
    )

    if gate is None:
        gate = LifecycleGate(
            id=uuid4(),
            project_id=project_id,
            phase_id=phase.id,
            phase_code=phase.phase_code,
            gate_code=gate_code,
            name=_derive_gate_name(phase, which, gate_code),
            description=phase.description,
            sequence=1 if which == "entry" else 2,
            status=new_status,
            context={},
        )
        session.add(gate)
    else:
        gate.phase_id = phase.id
        gate.status = new_status
        if not gate.name:
            gate.name = _derive_gate_name(phase, which, gate_code)
        if gate.sequence is None:
            gate.sequence = 1 if which == "entry" else 2

    approver_uuid = approver_user_id
    if not isinstance(approver_uuid, UUID):
        approver_uuid = UUID(str(approver_user_id))

    approval = LifecycleGateApproval(
        id=uuid4(),
        gate=gate,
        approver_user_id=approver_uuid,
        role_key=role_key,
        decision=decision,
        comment=comment,
        status=decision.value,
        decided_by=approver_uuid,
        decided_at=datetime.now(timezone.utc),
    )
    session.add(approval)

    if gate.status == GateStatus.APPROVED:
        emit_phase_milestone(
            project_id,
            phase_code=phase_code,
            gate_code=gate_code,
            event_type="gate.approved",
            comment=comment,
        )

    return gate, approval
