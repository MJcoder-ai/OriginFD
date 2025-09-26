"""Composable lifecycle response builder."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.models.lifecycle import GateStatus, LifecycleGate, LifecyclePhase


def build_lifecycle_view(session: Session, project_id) -> List[Dict[str, Any]]:
    """Compose the lifecycle response for a project from DB rows only."""

    phases = session.scalars(
        select(LifecyclePhase)
        .where(LifecyclePhase.project_id == project_id)
        .order_by(LifecyclePhase.order)
    ).all()

    gates = session.scalars(
        select(LifecycleGate).where(LifecycleGate.project_id == project_id)
    ).all()
    gmap = {(gate.phase_code, gate.gate_code): gate for gate in gates}

    def _gate_payload(phase_code: int, gate_code: str) -> Dict[str, Any]:
        gate = gmap.get((phase_code, gate_code))
        status = (
            gate.status.value
            if gate and hasattr(gate.status, "value")
            else (gate.status if gate else GateStatus.NOT_STARTED.value)
        )
        return {"gate_code": gate_code, "status": status}

    out: List[Dict[str, Any]] = []
    for phase in phases:
        entry_payload = _gate_payload(phase.phase_code, phase.entry_gate_code)
        exit_payload = _gate_payload(phase.phase_code, phase.exit_gate_code)

        out.append(
            {
                "phase_code": phase.phase_code,
                "phase_key": phase.phase_key,
                "title": phase.title,
                "order": phase.order,
                "entry_gate_code": phase.entry_gate_code,
                "exit_gate_code": phase.exit_gate_code,
                "required_entry_roles": phase.required_entry_roles or [],
                "required_exit_roles": phase.required_exit_roles or [],
                "odl_sd_sections": phase.odl_sd_sections or [],
                "name": phase.title,
                "status": "not_started",
                "gates": [
                    {
                        "key": phase.entry_gate_code,
                        "name": "Entry",
                        **entry_payload,
                    },
                    {
                        "key": phase.exit_gate_code,
                        "name": "Exit",
                        **exit_payload,
                    },
                ],
            }
        )

    return out
