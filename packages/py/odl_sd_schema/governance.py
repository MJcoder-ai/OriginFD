"""Governance and approval models for ODL-SD."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Signature(BaseModel):
    """Digital signature for approvals."""

    signer: str
    role: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Approval(BaseModel):
    """Approval record containing signatures."""

    id: str
    description: Optional[str] = None
    signatures: List[Signature] = Field(default_factory=list)


class Governance(BaseModel):
    """Governance information for the document."""

    approvals: List[Approval] = Field(default_factory=list)
