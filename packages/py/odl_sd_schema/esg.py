"""Environmental, social and governance models for ODL-SD."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ESGMetric(BaseModel):
    """Single ESG metric entry."""

    name: str
    value: float
    unit: Optional[str] = None


class ESGMetrics(BaseModel):
    """Collection of ESG metrics."""

    metrics: List[ESGMetric] = Field(default_factory=list)


class ESG(BaseModel):
    """Top level ESG section."""

    summary: Optional[str] = None
    metrics: ESGMetrics = Field(default_factory=ESGMetrics)
