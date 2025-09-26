"""
ODL-SD v4.1 Schema Definitions and Validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Domain(str, Enum):
    """Energy system domains"""

    PV = "PV"
    BESS = "BESS"
    HYBRID = "HYBRID"
    GRID = "GRID"
    MICROGRID = "MICROGRID"


class Scale(str, Enum):
    """Project scale types"""

    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    UTILITY = "UTILITY"
    HYPERSCALE = "HYPERSCALE"


class UnitSystem(BaseModel):
    """Unit system definition"""

    system: str = Field(default="SI", description="Unit system (SI, Imperial)")
    currency: str = Field(default="USD", description="Currency code")
    coordinate_system: str = Field(
        default="EPSG:4326", description="Coordinate reference system"
    )


class Timestamps(BaseModel):
    """Document timestamps"""

    created_at: str = Field(description="ISO 8601 timestamp")
    updated_at: str = Field(description="ISO 8601 timestamp")

    @validator("created_at", "updated_at")
    def validate_iso_timestamp(cls, v):
        """Validate ISO 8601 timestamp format"""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("Invalid ISO 8601 timestamp format")


class Versioning(BaseModel):
    """Document versioning information"""

    document_version: str = Field(description="Document version (e.g., 4.1.0)")
    content_hash: str = Field(description="SHA256 hash of content")


class MetaData(BaseModel):
    """ODL-SD document metadata"""

    project: str = Field(description="Project name")
    domain: Domain = Field(description="System domain")
    scale: Scale = Field(description="Project scale")
    units: UnitSystem = Field(default_factory=UnitSystem)
    timestamps: Timestamps
    versioning: Versioning


class PortfolioHierarchy(BaseModel):
    """Portfolio hierarchy definition"""

    id: str = Field(description="Unique portfolio identifier")
    name: str = Field(description="Portfolio name")
    description: Optional[str] = Field(description="Portfolio description")
    location: Optional[str] = Field(description="Portfolio location")


class FunctionalRequirements(BaseModel):
    """Functional requirements specification"""

    capacity_kw: Optional[float] = Field(
        default=None, description="System capacity in kW", ge=0
    )
    annual_generation_kwh: Optional[float] = Field(
        default=None, description="Annual energy generation in kWh", ge=0
    )
    performance_requirements: Dict[str, Any] = Field(default_factory=dict)


class TechnicalRequirements(BaseModel):
    """Technical requirements specification"""

    grid_connection: bool = Field(default=True, description="Grid connection required")
    voltage_level: Optional[str] = Field(
        None, description="Voltage level specification"
    )
    frequency_hz: Optional[float] = Field(
        None, description="System frequency in Hz", ge=0
    )


class RegulatoryRequirements(BaseModel):
    """Regulatory requirements"""

    grid_codes: List[str] = Field(
        default_factory=list, description="Applicable grid codes"
    )
    safety_standards: List[str] = Field(
        default_factory=list, description="Safety standards"
    )
    environmental_permits: List[str] = Field(
        default_factory=list, description="Environmental permits"
    )


class Requirements(BaseModel):
    """System requirements"""

    functional: FunctionalRequirements = Field(default_factory=FunctionalRequirements)
    technical: TechnicalRequirements = Field(default_factory=TechnicalRequirements)
    regulatory: RegulatoryRequirements = Field(default_factory=RegulatoryRequirements)


class DataManagement(BaseModel):
    """Data management configuration"""

    partitioning_enabled: bool = Field(
        default=False, description="Enable data partitioning"
    )
    external_refs_enabled: bool = Field(
        default=False, description="Enable external references"
    )
    streaming_enabled: bool = Field(default=False, description="Enable streaming data")
    max_document_size_mb: int = Field(
        default=100, description="Maximum document size in MB", ge=1
    )


class ComponentInstance(BaseModel):
    """Component instance definition"""

    id: str = Field(description="Unique instance identifier")
    type: str = Field(description="Component type")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Instance parameters"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Instance metadata"
    )


class Connection(BaseModel):
    """System connection definition"""

    id: str = Field(description="Unique connection identifier")
    from_component: str = Field(description="Source component ID")
    to_component: str = Field(description="Target component ID")
    connection_type: str = Field(description="Connection type")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Connection parameters"
    )


class AnalysisResult(BaseModel):
    """Analysis result definition"""

    id: str = Field(description="Unique analysis identifier")
    type: str = Field(description="Analysis type")
    timestamp: str = Field(description="Analysis timestamp")
    results: Dict[str, Any] = Field(description="Analysis results")


class AuditEntry(BaseModel):
    """Audit trail entry"""

    timestamp: str = Field(description="Entry timestamp")
    action: str = Field(description="Action performed")
    user_id: str = Field(description="User who performed the action")
    changes: Dict[str, Any] = Field(default_factory=dict, description="Changes made")


class OdlSdDocument(BaseModel):
    """ODL-SD v4.1 Document Schema"""

    schema_url: str = Field(
        alias="$schema",
        default="https://odl-sd.org/schemas/v4.1/document.json",
        description="JSON Schema URL",
    )
    schema_version: str = Field(default="4.1", description="ODL-SD schema version")
    meta: MetaData = Field(description="Document metadata")
    hierarchy: Dict[str, Any] = Field(
        default_factory=dict, description="System hierarchy"
    )
    requirements: Requirements = Field(
        default_factory=Requirements, description="System requirements"
    )
    libraries: Dict[str, Any] = Field(
        default_factory=dict, description="Component libraries"
    )
    instances: List[ComponentInstance] = Field(
        default_factory=list, description="Component instances"
    )
    connections: List[Connection] = Field(
        default_factory=list, description="System connections"
    )
    analysis: List[AnalysisResult] = Field(
        default_factory=list, description="Analysis results"
    )
    audit: List[AuditEntry] = Field(default_factory=list, description="Audit trail")
    data_management: DataManagement = Field(
        default_factory=DataManagement, description="Data management config"
    )

    class Config:
        validate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    def validate_document(self) -> tuple[bool, List[str]]:
        """
        Validate the ODL-SD document
        Returns: (is_valid, error_messages)
        """
        errors = []

        try:
            # Validate required fields
            if not self.meta.project:
                errors.append("Project name is required")

            # Validate hierarchy structure
            if not self.hierarchy:
                errors.append("Hierarchy definition is required")

            # Validate instance references
            instance_ids = {inst.id for inst in self.instances}
            for connection in self.connections:
                if connection.from_component not in instance_ids:
                    errors.append(
                        f"Connection references unknown component: {connection.from_component}"
                    )
                if connection.to_component not in instance_ids:
                    errors.append(
                        f"Connection references unknown component: {connection.to_component}"
                    )

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return self.dict(by_alias=True, exclude_none=False)
