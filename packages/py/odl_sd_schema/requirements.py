"""Requirement models for ODL-SD documents."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FunctionalRequirement(BaseModel):
    """Individual functional requirement entry."""

    id: str
    description: str
    priority: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Priority scale 1 (low) - 5 (high)",
    )
    reference: Optional[str] = Field(
        default=None,
        description="External reference or specification link",
    )


class FunctionalRequirements(BaseModel):
    """Container for functional requirements."""

    items: List[FunctionalRequirement] = Field(default_factory=list)


class Requirements(BaseModel):
    """Top level requirements section of an ODL-SD document."""

    functional: FunctionalRequirements = Field(
        default_factory=FunctionalRequirements
    )
    constraints: Dict[str, Any] = Field(default_factory=dict)
    regulatory: List[str] = Field(default_factory=list)
    esg: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"
