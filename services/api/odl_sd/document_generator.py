"""
ODL-SD Document Generator
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from .schemas import (
    OdlSdDocument, MetaData, Timestamps, Versioning, UnitSystem,
    PortfolioHierarchy, Requirements, FunctionalRequirements, 
    TechnicalRequirements, RegulatoryRequirements, DataManagement,
    ComponentInstance, Connection, AuditEntry, Domain, Scale
)


class DocumentGenerator:
    """Generate ODL-SD documents from project data"""
    
    @staticmethod
    def generate_content_hash(content: Dict[str, Any]) -> str:
        """Generate SHA256 hash of document content"""
        content_str = json.dumps(content, sort_keys=True)
        return f"sha256:{hashlib.sha256(content_str.encode()).hexdigest()}"
    
    @staticmethod
    def create_base_document(
        project_name: str,
        domain: str,
        scale: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        capacity_kw: Optional[float] = None
    ) -> OdlSdDocument:
        """Create a base ODL-SD document from project parameters"""
        
        current_time = datetime.utcnow().isoformat() + "Z"
        
        # Create metadata
        meta = MetaData(
            project=project_name,
            domain=Domain(domain),
            scale=Scale(scale),
            units=UnitSystem(),
            timestamps=Timestamps(
                created_at=current_time,
                updated_at=current_time
            ),
            versioning=Versioning(
                document_version="4.1.0",
                content_hash="sha256:" + "0" * 64  # Will be calculated later
            )
        )
        
        # Create hierarchy
        hierarchy = {
            "portfolio": {
                "id": f"portfolio-{str(uuid4())[:8]}",
                "name": project_name,
                "description": description or f"{domain} {scale} project",
                "location": location or "TBD"
            }
        }
        
        # Create functional requirements
        functional_req = FunctionalRequirements()
        if capacity_kw:
            functional_req.capacity_kw = capacity_kw
            
        # Create technical requirements based on domain
        technical_req = TechnicalRequirements()
        if domain == "MICROGRID":
            technical_req.grid_connection = False
        else:
            technical_req.grid_connection = True
            
        # Set default frequency based on region (assume 60Hz for now)
        technical_req.frequency_hz = 60.0
        
        # Create regulatory requirements
        regulatory_req = RegulatoryRequirements()
        
        # Add domain-specific grid codes
        if domain in ["PV", "HYBRID"]:
            regulatory_req.grid_codes.append("IEEE 1547")
            regulatory_req.safety_standards.append("IEC 61730")
        if domain in ["BESS", "HYBRID"]:
            regulatory_req.grid_codes.append("IEEE 1547.1")
            regulatory_req.safety_standards.append("UL 1973")
        
        requirements = Requirements(
            functional=functional_req,
            technical=technical_req,
            regulatory=regulatory_req
        )
        
        # Create document
        document = OdlSdDocument(
            meta=meta,
            hierarchy=hierarchy,
            requirements=requirements,
            libraries={},
            instances=[],
            connections=[],
            analysis=[],
            audit=[],
            data_management=DataManagement()
        )
        
        # Calculate and set content hash
        content_dict = document.to_dict()
        content_hash = DocumentGenerator.generate_content_hash(content_dict)
        document.meta.versioning.content_hash = content_hash
        
        return document
    
    @staticmethod
    def add_pv_components(document: OdlSdDocument, capacity_kw: float) -> OdlSdDocument:
        """Add PV system components to the document"""
        
        # Add PV array instance
        pv_array = ComponentInstance(
            id="pv_array_1",
            type="pv_array",
            parameters={
                "capacity_kw": capacity_kw,
                "module_type": "c-Si",
                "tracking": "fixed",
                "tilt_angle": 25,
                "azimuth": 180
            },
            metadata={
                "manufacturer": "TBD",
                "model": "TBD",
                "efficiency": 0.20
            }
        )
        document.instances.append(pv_array)
        
        # Add inverter instance
        inverter = ComponentInstance(
            id="inverter_1", 
            type="inverter",
            parameters={
                "capacity_kw": capacity_kw * 0.95,  # DC/AC ratio
                "efficiency": 0.98,
                "type": "string"
            },
            metadata={
                "manufacturer": "TBD",
                "model": "TBD"
            }
        )
        document.instances.append(inverter)
        
        # Add connection between PV and inverter
        pv_inverter_connection = Connection(
            id="pv_inv_conn_1",
            from_component="pv_array_1",
            to_component="inverter_1", 
            connection_type="dc_electrical",
            parameters={
                "voltage_range": "600-1500V",
                "current_max": capacity_kw / 800 * 1000  # Approximate DC current
            }
        )
        document.connections.append(pv_inverter_connection)
        
        return document
    
    @staticmethod
    def add_bess_components(document: OdlSdDocument, capacity_kw: float, duration_hours: float = 4.0) -> OdlSdDocument:
        """Add battery energy storage system components"""
        
        energy_kwh = capacity_kw * duration_hours
        
        # Add battery instance
        battery = ComponentInstance(
            id="battery_1",
            type="battery",
            parameters={
                "capacity_kwh": energy_kwh,
                "power_kw": capacity_kw,
                "chemistry": "lithium_ion",
                "voltage_nominal": 400,
                "efficiency_roundtrip": 0.90
            },
            metadata={
                "manufacturer": "TBD",
                "model": "TBD",
                "cycle_life": 6000
            }
        )
        document.instances.append(battery)
        
        # Add battery inverter/PCS
        pcs = ComponentInstance(
            id="pcs_1",
            type="power_conversion_system", 
            parameters={
                "capacity_kw": capacity_kw,
                "efficiency": 0.95,
                "bidirectional": True
            },
            metadata={
                "manufacturer": "TBD",
                "model": "TBD"
            }
        )
        document.instances.append(pcs)
        
        # Add connection between battery and PCS
        batt_pcs_connection = Connection(
            id="batt_pcs_conn_1",
            from_component="battery_1",
            to_component="pcs_1",
            connection_type="dc_electrical",
            parameters={
                "voltage_range": "300-500V",
                "current_max": capacity_kw / 400 * 1000  # Approximate DC current
            }
        )
        document.connections.append(batt_pcs_connection)
        
        return document
    
    @staticmethod
    def add_audit_entry(document: OdlSdDocument, action: str, user_id: str, changes: Optional[Dict] = None) -> OdlSdDocument:
        """Add audit entry to document"""
        
        audit_entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            action=action,
            user_id=user_id,
            changes=changes or {}
        )
        document.audit.append(audit_entry)
        
        # Update document timestamp and hash
        document.meta.timestamps.updated_at = datetime.utcnow().isoformat() + "Z"
        content_dict = document.to_dict()
        document.meta.versioning.content_hash = DocumentGenerator.generate_content_hash(content_dict)
        
        return document
    
    @staticmethod
    def create_project_document(
        project_name: str,
        domain: str,
        scale: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        capacity_kw: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> OdlSdDocument:
        """Create a complete ODL-SD document for a project"""
        
        # Create base document
        document = DocumentGenerator.create_base_document(
            project_name=project_name,
            domain=domain,
            scale=scale,
            description=description,
            location=location,
            capacity_kw=capacity_kw
        )
        
        # Add domain-specific components
        if capacity_kw and capacity_kw > 0:
            if domain == "PV":
                document = DocumentGenerator.add_pv_components(document, capacity_kw)
            elif domain == "BESS":
                document = DocumentGenerator.add_bess_components(document, capacity_kw)
            elif domain == "HYBRID":
                # For hybrid systems, split capacity between PV and BESS
                pv_capacity = capacity_kw * 0.7  # 70% PV
                bess_capacity = capacity_kw * 0.3  # 30% BESS
                document = DocumentGenerator.add_pv_components(document, pv_capacity)
                document = DocumentGenerator.add_bess_components(document, bess_capacity, 2.0)  # 2-hour duration
        
        # Add initial audit entry
        if user_id:
            document = DocumentGenerator.add_audit_entry(
                document, 
                "document_created",
                user_id,
                {"initial_creation": True}
            )
        
        return document