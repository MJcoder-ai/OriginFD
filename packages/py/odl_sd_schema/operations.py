"""Operations and monitoring models for ODL-SD."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Monitoring(BaseModel):
    """Monitoring configuration for a system."""

    telemetry: List[str] = Field(default_factory=list)
    availability_target: Optional[float] = None


class Operations(BaseModel):
    """Operational information for the asset."""

    maintenance_schedule: Optional[str] = None
    monitoring: Monitoring = Field(default_factory=Monitoring)
