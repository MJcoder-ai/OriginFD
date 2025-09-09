"""Financial modeling structures for ODL-SD."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FinancialModel(BaseModel):
    """A named financial model with assumptions and results."""

    name: str
    assumptions: Dict[str, float] = Field(default_factory=dict)
    results: Dict[str, float] = Field(default_factory=dict)


class Finance(BaseModel):
    """Finance section including capital and operational costs."""

    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    capex: Optional[float] = None
    opex: Optional[float] = None
    models: List[FinancialModel] = Field(default_factory=list)
