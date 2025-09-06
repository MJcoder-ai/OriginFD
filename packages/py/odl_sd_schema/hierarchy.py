"""
Hierarchical organization models for ODL-SD documents.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class HierarchyType(str, Enum):
    """Hierarchy node types."""
    PORTFOLIO = "PORTFOLIO"
    SITE = "SITE"
    PLANT = "PLANT"
    BLOCK = "BLOCK"
    ARRAY = "ARRAY"
    STRING = "STRING"
    DEVICE = "DEVICE"


class Portfolio(BaseModel):
    """Portfolio-level configuration."""
    id: str
    name: str
    total_capacity_gw: float
    regions: Dict[str, Dict] = Field(default_factory=dict)
    
    @validator("total_capacity_gw")
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("Portfolio capacity must be positive")
        return v


class Site(BaseModel):
    """Site-level configuration."""
    id: str
    name: str
    location: Dict[str, float]  # lat, lon, elevation
    timezone: str
    capacity_mw: float
    
    @validator("location")
    def validate_location(cls, v):
        required_keys = ["lat", "lon"]
        if not all(key in v for key in required_keys):
            raise ValueError("Location must include lat and lon")
        
        if not (-90 <= v["lat"] <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= v["lon"] <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        
        return v
    
    @validator("capacity_mw")
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("Site capacity must be positive")
        return v


class Plant(BaseModel):
    """Plant-level configuration."""
    id: str
    name: str
    site_id: str
    plant_type: str  # "PV", "BESS", "HYBRID"
    capacity_mw: float
    interconnection_voltage_kv: float
    
    @validator("capacity_mw")
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("Plant capacity must be positive")
        return v
    
    @validator("interconnection_voltage_kv")
    def validate_voltage(cls, v):
        if v <= 0:
            raise ValueError("Interconnection voltage must be positive")
        return v


class Block(BaseModel):
    """Block-level configuration."""
    id: str
    name: str
    plant_id: str
    capacity_mw: float
    dc_ac_ratio: Optional[float] = None
    
    @validator("capacity_mw")
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("Block capacity must be positive")
        return v
    
    @validator("dc_ac_ratio")
    def validate_dc_ac_ratio(cls, v):
        if v is not None and v <= 0:
            raise ValueError("DC/AC ratio must be positive")
        return v


class Hierarchy(BaseModel):
    """
    Hierarchical organization structure.
    Defines the portfolio -> site -> plant -> block structure.
    """
    type: HierarchyType
    id: str
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    
    # Type-specific data
    portfolio: Optional[Portfolio] = None
    site: Optional[Site] = None
    plant: Optional[Plant] = None
    block: Optional[Block] = None
    
    class Config:
        extra = "forbid"
    
    @validator("children")
    def validate_children_not_self(cls, v, values):
        """Ensure children don't include self."""
        if "id" in values and values["id"] in v:
            raise ValueError("Node cannot be its own child")
        return v
    
    def get_capacity_mw(self) -> Optional[float]:
        """Get capacity based on hierarchy type."""
        if self.type == HierarchyType.PORTFOLIO and self.portfolio:
            return self.portfolio.total_capacity_gw * 1000
        elif self.type == HierarchyType.SITE and self.site:
            return self.site.capacity_mw
        elif self.type == HierarchyType.PLANT and self.plant:
            return self.plant.capacity_mw
        elif self.type == HierarchyType.BLOCK and self.block:
            return self.block.capacity_mw
        return None
    
    def get_location(self) -> Optional[Dict[str, float]]:
        """Get location if available."""
        if self.type == HierarchyType.SITE and self.site:
            return self.site.location
        return None
    
    def add_child(self, child_id: str):
        """Add a child node."""
        if child_id not in self.children:
            self.children.append(child_id)
    
    def remove_child(self, child_id: str):
        """Remove a child node."""
        if child_id in self.children:
            self.children.remove(child_id)