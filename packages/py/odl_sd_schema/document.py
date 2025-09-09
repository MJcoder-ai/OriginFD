"""
Core ODL-SD document model and metadata structures.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from .hierarchy import Hierarchy
from .requirements import Requirements
from .libraries import ComponentLibrary
from .instances import ComponentInstance
from .connections import Connection
from .analysis import Analysis
from .finance import Finance
from .operations import Operations
from .esg import ESG
from .governance import Governance


class Domain(str, Enum):
    """Supported system domains."""
    PV = "PV"
    BESS = "BESS"
    HYBRID = "HYBRID"
    GRID = "GRID"
    MICROGRID = "MICROGRID"


class Scale(str, Enum):
    """System scale categories."""
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    UTILITY = "UTILITY"
    HYPERSCALE = "HYPERSCALE"


class UnitSystem(str, Enum):
    """Unit system options."""
    SI = "SI"
    IMPERIAL = "IMPERIAL"


class Units(BaseModel):
    """Unit system configuration."""
    system: UnitSystem = UnitSystem.SI
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    coordinate_system: str = Field(default="EPSG:4326")


class Timestamps(BaseModel):
    """Document timestamps."""
    created_at: datetime
    updated_at: datetime
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class Versioning(BaseModel):
    """Document versioning information."""
    document_version: str = Field(default="4.1.0")
    content_hash: str = Field(pattern="^sha256:[a-f0-9]{64}$")
    previous_hash: Optional[str] = Field(default=None, pattern="^sha256:[a-f0-9]{64}$")
    change_summary: Optional[str] = None


class DocumentMeta(BaseModel):
    """Document metadata."""
    project: str
    portfolio_id: Optional[str] = None
    domain: Domain
    scale: Scale
    units: Units = Field(default_factory=Units)
    timestamps: Timestamps
    versioning: Versioning
    
    @validator("project")
    def validate_project_name(cls, v):
        """Validate project name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Project name cannot be empty")
        if len(v) > 255:
            raise ValueError("Project name too long")
        return v.strip()


class DataManagement(BaseModel):
    """Data management strategies for large documents."""
    partitioning_enabled: bool = False
    partition_strategy: Optional[str] = None
    external_refs_enabled: bool = False
    streaming_enabled: bool = False
    max_document_size_mb: int = 100
    
    class Config:
        extra = "allow"


class OdlDocument(BaseModel):
    """
    Complete ODL-SD v4.1 document structure.
    Root model for all energy system representations.
    """
    schema_: str = Field(
        default="https://odl-sd.org/schemas/v4.1/document.json",
        alias="$schema"
    )
    schema_version: str = Field(default="4.1")
    
    # Core sections
    meta: DocumentMeta
    hierarchy: Optional[Hierarchy] = None
    requirements: Optional[Requirements] = None
    libraries: Optional[Dict[str, ComponentLibrary]] = Field(default_factory=dict)
    instances: List[ComponentInstance] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)
    
    # Extended sections
    structures: Optional[Dict[str, Any]] = Field(default_factory=dict)
    physical: Optional[Dict[str, Any]] = Field(default_factory=dict)
    analysis: List[Analysis] = Field(default_factory=list)
    compliance: Optional[Dict[str, Any]] = Field(default_factory=dict)
    finance: Optional[Finance] = None
    operations: Optional[Operations] = None
    esg: Optional[ESG] = None
    governance: Optional[Governance] = None
    
    # External integrations
    external_models: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # System sections
    audit: List[Dict[str, Any]] = Field(default_factory=list)
    data_management: DataManagement = Field(default_factory=DataManagement)
    
    class Config:
        allow_population_by_field_name = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator("schema_version")
    def validate_schema_version(cls, v):
        """Ensure schema version is supported."""
        if v != "4.1":
            raise ValueError("Only schema version 4.1 is supported")
        return v
    
    @validator("instances")
    def validate_instances_unique_ids(cls, v):
        """Ensure all instance IDs are unique."""
        ids = [instance.id for instance in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Instance IDs must be unique")
        return v
    
    @validator("connections")
    def validate_connections_reference_instances(cls, v, values):
        """Ensure connections reference valid instances."""
        if "instances" not in values:
            return v
        
        instance_ids = {instance.id for instance in values["instances"]}
        
        for connection in v:
            if connection.from_instance_id not in instance_ids:
                raise ValueError(f"Connection references unknown instance: {connection.from_instance_id}")
            if connection.to_instance_id not in instance_ids:
                raise ValueError(f"Connection references unknown instance: {connection.to_instance_id}")
        
        return v
    
    def get_version(self) -> int:
        """Get document version number for optimistic concurrency."""
        return len(self.audit)
    
    def add_audit_entry(self, action: str, actor: str, details: Optional[Dict] = None):
        """Add audit entry for document changes."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "version": self.get_version() + 1,
            "details": details or {}
        }
        self.audit.append(entry)
        self.meta.timestamps.updated_at = datetime.utcnow()
    
    def save_to_dict(self) -> Dict[str, Any]:
        """Export document to dictionary format."""
        return self.dict(by_alias=True, exclude_none=True)
    
    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "OdlDocument":
        """Load document from dictionary format."""
        return cls.parse_obj(data)