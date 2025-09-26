"""Endpoints for handling project change approvals."""

from __future__ import annotations

from typing import Any, Dict, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

# Temporarily disabled - import issue
# from services.commerce_core import publish_usage_event

# Temporarily disabled due to import issues:
# from packages.py.odl_sd_patch.diff_utils import generate_diff_summary

router = APIRouter()


APPROVAL_DECISION_PSU_CHARGE = 10


class ApprovalRequest(BaseModel):
    """Request body for approval decisions."""

    project_id: str = Field(..., description="Project identifier")
    decision: Literal["approve", "reject"]
    source: Dict[str, Any]
    target: Dict[str, Any]


class ApprovalResponse(BaseModel):
    """Response model including diff summary."""

    project_id: str
    decision: str
    grouped_diffs: Dict[str, Any]
    kpi_deltas: Dict[str, float]


@router.post("/", response_model=ApprovalResponse)
async def handle_approval(req: ApprovalRequest) -> ApprovalResponse:
    """Process an approval decision and return diff information."""
    # TODO: Implement generate_diff_summary when package is available
    # summary = generate_diff_summary(req.source, req.target)
    summary = {"grouped_diffs": {}, "kpi_deltas": {}}  # Temporary placeholder
    _ = _resolve_tenant_id(req.source) or _resolve_tenant_id(req.target)
    _ = {
        "event": "gate_approval",
        "project_id": req.project_id,
        "decision": req.decision,
        "has_summary": bool(summary["grouped_diffs"]),
    }
    # Temporarily disabled - publish_usage_event call
    # publish_usage_event(
    #     tenant_id or "00000000-0000-0000-0000-000000000000",
    #     APPROVAL_DECISION_PSU_CHARGE,
    #     metadata,
    # )
    return ApprovalResponse(
        project_id=req.project_id,
        decision=req.decision,
        grouped_diffs=summary["grouped_diffs"],
        kpi_deltas=summary["kpi_deltas"],
    )


def _resolve_tenant_id(payload: Dict[str, Any]) -> str | None:
    """Extract a tenant identifier from nested payload structures."""
    if not isinstance(payload, dict):
        return None

    candidate = payload.get("tenant_id")
    if candidate:
        return str(candidate)

    context = payload.get("context")
    if isinstance(context, dict) and context.get("tenant_id"):
        return str(context["tenant_id"])

    return None
