from __future__ import annotations

from typing import List

from pydantic import BaseModel


class LifecyclePhaseSpec(BaseModel):
    """Immutable specification for a project lifecycle phase."""

    phase_code: int
    phase_key: str
    title: str
    order: int
    entry_gate_code: str
    exit_gate_code: str
    required_entry_roles: List[str]
    required_exit_roles: List[str]
    odl_sd_sections: List[str]
    description: str

    class Config:
        frozen = True


LIFECYCLE_CATALOG: List[LifecyclePhaseSpec] = [
    LifecyclePhaseSpec(
        phase_code=0,
        phase_key="phase.discovery",
        title="Discovery & Qualification",
        order=0,
        entry_gate_code="G0",
        exit_gate_code="G1",
        required_entry_roles=["role.project_manager", "role.exec.sponsor"],
        required_exit_roles=["role.project_manager", "role.engineer.lead"],
        odl_sd_sections=[
            "odl.project_charter",
            "odl.requirements",
            "odl.risk_register",
            "odl.financial_model",
        ],
        description=(
            "Confirm opportunity intent, tariffs, and viability with "
            "sponsor approval to progress."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=1,
        phase_key="phase.concept_feasibility",
        title="Concept & Feasibility",
        order=1,
        entry_gate_code="G1",
        exit_gate_code="G2",
        required_entry_roles=["role.project_manager", "role.engineer.lead"],
        required_exit_roles=["role.engineer.lead", "role.finops"],
        odl_sd_sections=[
            "odl.site_assessment",
            "odl.risk_register",
            "odl.financial_model",
        ],
        description=(
            "Develop concept scenarios, resource models, and prelim "
            "economics to secure feasibility signoff."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=2,
        phase_key="phase.requirements_scope",
        title="Requirements & Scope",
        order=2,
        entry_gate_code="G2",
        exit_gate_code="G3",
        required_entry_roles=["role.project_manager", "role.engineer.lead"],
        required_exit_roles=["role.project_manager", "role.compliance"],
        odl_sd_sections=[
            "odl.requirements",
            "odl.project_charter",
            "odl.hse_plan",
        ],
        description=(
            "Lock functional, regulatory, and HSE scope baselines before "
            "issuing design directives."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=3,
        phase_key="phase.preliminary_design",
        title="Preliminary Design",
        order=3,
        entry_gate_code="G3",
        exit_gate_code="G4",
        required_entry_roles=["role.engineer.lead", "role.project_manager"],
        required_exit_roles=["role.engineer.lead", "role.qa"],
        odl_sd_sections=[
            "odl.electrical_design",
            "odl.site_assessment",
            "odl.risk_register",
        ],
        description=(
            "Produce concept layouts, array topologies, and design risks "
            "for multidisciplinary review."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=4,
        phase_key="phase.detailed_design",
        title="Detailed Design",
        order=4,
        entry_gate_code="G4",
        exit_gate_code="G5",
        required_entry_roles=["role.engineer.lead", "role.qa"],
        required_exit_roles=["role.engineer.lead", "role.compliance"],
        odl_sd_sections=[
            "odl.electrical_design",
            "odl.qa_qc_plan",
            "odl.hse_plan",
            "odl.requirements",
        ],
        description=(
            "Complete IFC designs, protections, and compliance packages "
            "ready for procurement release."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=5,
        phase_key="phase.procurement_planning",
        title="Procurement Planning",
        order=5,
        entry_gate_code="G5",
        exit_gate_code="G6",
        required_entry_roles=["role.project_manager", "role.finops"],
        required_exit_roles=["role.procurement", "role.finops"],
        odl_sd_sections=[
            "odl.procurement_plan",
            "odl.financial_model",
            "odl.risk_register",
        ],
        description=(
            "Finalize sourcing strategy, budgets, and risk mitigations for "
            "RFQ issuance."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=6,
        phase_key="phase.supplier_selection",
        title="Supplier Selection & POs",
        order=6,
        entry_gate_code="G6",
        exit_gate_code="G7",
        required_entry_roles=["role.procurement", "role.finops"],
        required_exit_roles=["role.procurement", "role.project_manager"],
        odl_sd_sections=[
            "odl.supplier_selection",
            "odl.procurement_plan",
            "odl.financial_model",
        ],
        description=(
            "Evaluate bids, secure vendor alignments, and execute purchase "
            "commitments."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=7,
        phase_key="phase.construction_installation",
        title="Construction & Installation",
        order=7,
        entry_gate_code="G7",
        exit_gate_code="G8",
        required_entry_roles=["role.construction", "role.project_manager"],
        required_exit_roles=["role.construction", "role.qa"],
        odl_sd_sections=[
            "odl.construction_method",
            "odl.qa_qc_plan",
            "odl.hse_plan",
        ],
        description=(
            "Execute field works, manage crews, and track install progress "
            "against plan."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=8,
        phase_key="phase.qa_precommission",
        title="QA/QC & Pre-Commission",
        order=8,
        entry_gate_code="G8",
        exit_gate_code="G9",
        required_entry_roles=["role.qa", "role.construction"],
        required_exit_roles=["role.qa", "role.compliance"],
        odl_sd_sections=[
            "odl.qa_qc_plan",
            "odl.commissioning",
            "odl.hse_plan",
        ],
        description=(
            "Run inspections, verify installation quality, and clear punch "
            "list blockers."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=9,
        phase_key="phase.commissioning_handover",
        title="Commissioning & Handover",
        order=9,
        entry_gate_code="G9",
        exit_gate_code="G10",
        required_entry_roles=["role.qa", "role.compliance"],
        required_exit_roles=["role.handover", "role.operations"],
        odl_sd_sections=[
            "odl.commissioning",
            "odl.handover_docs",
            "odl.qa_qc_plan",
        ],
        description=(
            "Complete functional tests, secure approvals, and handoff packages "
            "to operations."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=10,
        phase_key="phase.operations_optimization",
        title="Operations & Optimization",
        order=10,
        entry_gate_code="G10",
        exit_gate_code="G11",
        required_entry_roles=["role.operations", "role.project_manager"],
        required_exit_roles=["role.operations", "role.exec.sponsor"],
        odl_sd_sections=[
            "odl.ops_playbook",
            "odl.risk_register",
            "odl.qa_qc_plan",
        ],
        description=(
            "Monitor performance, resolve incidents, and drive continuous "
            "improvement targets."
        ),
    ),
    LifecyclePhaseSpec(
        phase_code=11,
        phase_key="phase.closeout",
        title="Closeout",
        order=11,
        entry_gate_code="G11",
        exit_gate_code="G12",
        required_entry_roles=["role.operations", "role.project_manager"],
        required_exit_roles=["role.exec.sponsor", "role.project_manager"],
        odl_sd_sections=[
            "odl.closeout_report",
            "odl.handover_docs",
            "odl.ops_playbook",
        ],
        description=(
            "Confirm contractual completion, archive knowledge, and release remaining "
            "obligations."
        ),
    ),
]
