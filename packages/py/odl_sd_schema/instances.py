"""Component instance models for ODL-SD."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator


class InstanceStatus(str, Enum):
    """Lifecycle status of a component instance."""

    PLANNED = "planned"
    INSTALLED = "installed"
    ACTIVE = "active"
    DECOMMISSIONED = "decommissioned"


class Location(BaseModel):
    """Geographic location for an instance."""

    lat: float
    lon: float
    elevation_m: Optional[float] = None

    @validator("lat")
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("lon")
    def validate_lon(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class ComponentInstance(BaseModel):
    """Instance of a component placed within a hierarchy."""

    id: str
    type_ref: str
    parent_ref: Optional[str] = None
    location: Optional[Location] = None
    lifecycle_status: InstanceStatus = InstanceStatus.PLANNED
