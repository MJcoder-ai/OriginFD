
"""Endpoints for handling project change approvals."""
from __future__ import annotations

from typing import Any, Dict, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from packages.py.odl_sd_patch.diff_utils import generate_diff_summary

router = APIRouter()


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
    summary = generate_diff_summary(req.source, req.target)
    return ApprovalResponse(
        project_id=req.project_id,
        decision=req.decision,
        grouped_diffs=summary["grouped_diffs"],
        kpi_deltas=summary["kpi_deltas"],
    )

