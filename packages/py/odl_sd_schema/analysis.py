"""Analysis models capturing simulations and calculations."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Result produced by an analysis."""

    metric: str
    value: float
    units: Optional[str] = None


class Analysis(BaseModel):
    """Single analysis entry with results."""

    id: str
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parameters: Dict[str, float] = Field(default_factory=dict)
    results: List[AnalysisResult] = Field(default_factory=list)
