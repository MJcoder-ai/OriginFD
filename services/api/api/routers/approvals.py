"""Endpoints for approving or rejecting project changes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ApprovalRequest(BaseModel):
    project_id: str
    approved: bool

class ApprovalResponse(BaseModel):
    project_id: str
    status: str

@router.post("/", response_model=ApprovalResponse)
async def submit_approval(request: ApprovalRequest) -> ApprovalResponse:
    """Record an approval or rejection for a project."""
    status = "approved" if request.approved else "rejected"
    return ApprovalResponse(project_id=request.project_id, status=status)
