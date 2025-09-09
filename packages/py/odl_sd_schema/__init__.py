"""ODL-SD Schema Package

Pydantic models and validation for ODL-SD v4.1 specification.
"""
from .document import OdlDocument, DocumentMeta, Versioning
from .hierarchy import Hierarchy, Portfolio, Site, Plant, Block
from .requirements import (
    Requirements,
    FunctionalRequirement,
    FunctionalRequirements,
)
from .libraries import (
    ComponentLibrary,
    Component,
    Port,
    SignalKind,
    Direction,
    Voltage,
    Signal,
)
from .instances import ComponentInstance, InstanceStatus, Location
from .connections import Connection, ConnectionType
from .analysis import Analysis, AnalysisResult
from .finance import Finance, FinancialModel
from .operations import Operations, Monitoring
from .esg import ESG, ESGMetrics, ESGMetric
from .governance import Governance, Approval, Signature
from .validation import validate_document, ValidationResult

__version__ = "0.1.0"

__all__ = [
    "OdlDocument",
    "DocumentMeta",
    "Versioning",
    "Hierarchy",
    "Portfolio",
    "Site",
    "Plant",
    "Block",
    "Requirements",
    "FunctionalRequirement",
    "FunctionalRequirements",
    "ComponentLibrary",
    "Component",
    "Port",
    "SignalKind",
    "Direction",
    "Voltage",
    "Signal",
    "ComponentInstance",
    "Location",
    "InstanceStatus",
    "Connection",
    "ConnectionType",
    "Analysis",
    "AnalysisResult",
    "Finance",
    "FinancialModel",
    "Operations",
    "Monitoring",
    "ESG",
    "ESGMetrics",
    "ESGMetric",
    "Governance",
    "Approval",
    "Signature",
    "validate_document",
    "ValidationResult",
]
