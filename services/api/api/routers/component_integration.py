"""
Component integration with ODL-SD documents.
Handles component bindings, project integration, and document updates.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import models
from deps import get_current_user
from core.database import SessionDep
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session

from packages.py.odl_sd_patch.patch import apply_patch, calculate_content_hash
from packages.py.odl_sd_schema.document import OdlDocument

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models


class ComponentBindingRequest(BaseModel):
    """Request model for binding components to ODL-SD documents."""

    component_id: str = Field(..., description="UUID of the component to bind")
    document_id: str = Field(..., description="UUID of the ODL-SD document")
    binding_type: str = Field(
        ..., description="Type of binding: 'library', 'instance', 'specification'"
    )
    location_path: str = Field(..., description="JSONPath to location in document")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional binding metadata"
    )


class ComponentBindingResponse(BaseModel):
    """Response model for component bindings."""

    id: str
    component_id: str
    document_id: str
    binding_type: str
    location_path: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectComponentRequest(BaseModel):
    """Request model for adding components to projects."""

    project_document_id: str = Field(
        ..., description="UUID of the project ODL-SD document"
    )
    components: List[Dict[str, Any]] = Field(
        ..., description="List of component instances to add"
    )
    location: str = Field(
        default="libraries.components", description="Location in ODL-SD document"
    )


class ComponentSpecificationRequest(BaseModel):
    """Request model for updating component specifications in documents."""

    component_id: str
    specifications: Dict[str, Any] = Field(
        ..., description="Component specifications to add/update"
    )
    merge_strategy: str = Field(
        default="deep_merge", description="How to merge specifications"
    )


# Component-Document Integration


@router.post(
    "/bind",
    response_model=ComponentBindingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bind_component_to_document(
    request: ComponentBindingRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Bind a component to an ODL-SD document at a specific location.
    """
    try:
        # Validate component exists and user has access
        component = (
            db.query(models.Component)
            .filter(
                and_(
                    models.Component.id == uuid.UUID(request.component_id),
                    models.Component.tenant_id == current_user["tenant_id"],
                )
            )
            .first()
        )

        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
            )

        # Validate document exists and user has access
        document = (
            db.query(models.Document)
            .filter(
                and_(
                    models.Document.id == uuid.UUID(request.document_id),
                    models.Document.tenant_id == current_user["tenant_id"],
                )
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Get current document content
        current_version = (
            db.query(models.DocumentVersion)
            .filter(models.DocumentVersion.document_id == document.id)
            .order_by(models.DocumentVersion.version_number.desc())
            .first()
        )

        if not current_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no versions",
            )

        # Parse ODL-SD document
        odl_document = OdlDocument.model_validate(current_version.document_data)

        # Create component reference based on binding type
        component_ref = create_component_reference(
            component, request.binding_type, request.metadata
        )

        # Apply component binding to document
        patch_ops = create_component_binding_patch(
            odl_document, component_ref, request.location_path, request.binding_type
        )

        # Apply patches to document
        updated_content = apply_patch(current_version.document_data, patch_ops)

        # Validate updated document
        updated_odl = OdlDocument.model_validate(updated_content)

        # Calculate new content hash and update versioning metadata
        new_hash = calculate_content_hash(updated_content)
        previous_hash = current_version.content_hash
        versioning_meta = updated_content.setdefault("meta", {}).setdefault(
            "versioning", {}
        )
        versioning_meta["previous_hash"] = previous_hash
        versioning_meta["content_hash"] = new_hash

        # Create new document version
        new_version = models.DocumentVersion(
            tenant_id=document.tenant_id,
            document_id=document.id,
            version_number=current_version.version_number + 1,
            content_hash=new_hash,
            previous_hash=previous_hash,
            change_summary=f"Added component binding: {component.name}",
            created_by=uuid.UUID(current_user["id"]),
            patch_operations=patch_ops,
            document_data=updated_content,
        )

        db.add(new_version)

        # Update document current version
        document.current_version = new_version.version_number
        document.content_hash = new_hash
        document.document_data = updated_content
        document.updated_at = datetime.utcnow()

        # Update component management with binding info
        if component.management:
            if not component.management.media:
                component.management.media = {
                    "library": [],
                    "capture_policy": {},
                    "doc_bindings": {"bindings": []},
                }

            binding_record = {
                "id": f"BIND-{uuid.uuid4().hex[:8].upper()}",
                "document_id": str(document.id),
                "document_name": document.project_name,
                "binding_type": request.binding_type,
                "location_path": request.location_path,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": request.metadata,
            }

            component.management.media["doc_bindings"]["bindings"].append(
                binding_record
            )
            component.management.add_audit_record(
                action="document_binding",
                actor_role="engineer",
                actor=current_user["email"],
                diff=f"Bound to document {document.project_name} at {request.location_path}",
            )

        db.commit()

        logger.info(
            f"Bound component {component.component_id} to document {document.project_name}"
        )

        return ComponentBindingResponse(
            id=binding_record["id"],
            component_id=request.component_id,
            document_id=request.document_id,
            binding_type=request.binding_type,
            location_path=request.location_path,
            metadata=request.metadata,
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to bind component to document: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bind component: {str(e)}",
        )


@router.post("/projects/add-components")
async def add_components_to_project(
    request: ProjectComponentRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Add multiple component instances to a project ODL-SD document.
    """
    try:
        # Get project document
        document = (
            db.query(models.Document)
            .filter(
                and_(
                    models.Document.id == uuid.UUID(request.project_document_id),
                    models.Document.tenant_id == current_user["tenant_id"],
                )
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project document not found",
            )

        # Get current version
        current_version = (
            db.query(models.DocumentVersion)
            .filter(models.DocumentVersion.document_id == document.id)
            .order_by(models.DocumentVersion.version_number.desc())
            .first()
        )

        # Parse ODL-SD document
        odl_document = OdlDocument.model_validate(current_version.document_data)

        # Ensure libraries.components exists
        if not hasattr(odl_document, "libraries") or not odl_document.libraries:
            odl_document.libraries = {"components": []}
        elif not hasattr(
            odl_document.libraries, "components"
        ) or not odl_document.libraries.get("components"):
            odl_document.libraries["components"] = []

        # Add component instances
        components_added = []
        for comp_data in request.components:
            component_id = comp_data.get("component_id")
            if not component_id:
                continue

            # Get component from database
            component = (
                db.query(models.Component)
                .filter(
                    and_(
                        models.Component.id == uuid.UUID(component_id),
                        models.Component.tenant_id == current_user["tenant_id"],
                    )
                )
                .first()
            )

            if not component:
                logger.warning(f"Component {component_id} not found, skipping")
                continue

            # Create component instance in ODL-SD format
            component_instance = create_odl_component_instance(component, comp_data)
            odl_document.libraries["components"].append(component_instance)
            components_added.append(component.name)

        # Create new document version
        new_content = odl_document.model_dump()
        previous_hash = current_version.content_hash
        versioning_meta = new_content.setdefault("meta", {}).setdefault(
            "versioning", {}
        )
        versioning_meta["previous_hash"] = previous_hash
        new_hash = calculate_content_hash(new_content)
        versioning_meta["content_hash"] = new_hash
        new_version = models.DocumentVersion(
            tenant_id=document.tenant_id,
            document_id=document.id,
            version_number=current_version.version_number + 1,
            content_hash=new_hash,
            previous_hash=previous_hash,
            change_summary=f"Added {len(components_added)} components: {', '.join(components_added)}",
            created_by=uuid.UUID(current_user["id"]),
            document_data=new_content,
        )

        db.add(new_version)

        # Update document
        document.current_version = new_version.version_number
        document.content_hash = new_hash
        document.document_data = new_content
        document.updated_at = datetime.utcnow()

        db.commit()

        logger.info(
            f"Added {len(components_added)} components to project {document.project_name}"
        )

        return {
            "message": f"Successfully added {len(components_added)} components to project",
            "components_added": components_added,
            "new_version": new_version.version_number,
        }

    except Exception as e:
        logger.error(f"Failed to add components to project: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add components: {str(e)}",
        )


@router.patch("/components/{component_id}/specifications")
async def update_component_specifications(
    component_id: str,
    request: ComponentSpecificationRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Update component specifications across all bound documents.
    """
    try:
        component = (
            db.query(models.Component)
            .filter(
                and_(
                    models.Component.id == uuid.UUID(component_id),
                    models.Component.tenant_id == current_user["tenant_id"],
                )
            )
            .first()
        )

        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
            )

        # Get all document bindings for this component
        bindings = []
        if component.management and component.management.media:
            bindings = component.management.media.get("doc_bindings", {}).get(
                "bindings", []
            )

        updated_documents = []

        # Update each bound document
        for binding in bindings:
            document_id = binding.get("document_id")
            if not document_id:
                continue

            try:
                document = (
                    db.query(models.Document)
                    .filter(models.Document.id == uuid.UUID(document_id))
                    .first()
                )

                if not document:
                    continue

                # Get current version
                current_version = (
                    db.query(models.DocumentVersion)
                    .filter(models.DocumentVersion.document_id == document.id)
                    .order_by(models.DocumentVersion.version_number.desc())
                    .first()
                )

                # Parse and update document
                odl_document = OdlDocument.model_validate(
                    current_version.document_data
                )

                # Update component specifications in document
                updated = update_component_specs_in_document(
                    odl_document,
                    component.component_id,
                    request.specifications,
                    request.merge_strategy,
                )

                if updated:
                    # Create new version
                    new_content = odl_document.model_dump()
                    previous_hash = current_version.content_hash
                    versioning_meta = new_content.setdefault("meta", {}).setdefault(
                        "versioning", {}
                    )
                    versioning_meta["previous_hash"] = previous_hash
                    new_hash = calculate_content_hash(new_content)
                    versioning_meta["content_hash"] = new_hash

                    new_version = models.DocumentVersion(
                        tenant_id=document.tenant_id,
                        document_id=document.id,
                        version_number=current_version.version_number + 1,
                        content_hash=new_hash,
                        previous_hash=previous_hash,
                        change_summary=f"Updated specifications for component {component.name}",
                        created_by=uuid.UUID(current_user["id"]),
                        document_data=new_content,
                    )

                    db.add(new_version)
                    document.current_version = new_version.version_number
                    document.content_hash = new_hash
                    document.document_data = new_content
                    document.updated_at = datetime.utcnow()

                    updated_documents.append(document.project_name)

            except Exception as e:
                logger.warning(f"Failed to update document {document_id}: {str(e)}")
                continue

        # Update component management
        if component.management:
            component.management.add_audit_record(
                action="specifications_update",
                actor_role="engineer",
                actor=current_user["email"],
                diff=f"Updated specifications in {len(updated_documents)} documents",
            )

        db.commit()

        return {
            "message": f"Updated specifications in {len(updated_documents)} documents",
            "updated_documents": updated_documents,
            "component_id": component_id,
        }

    except Exception as e:
        logger.error(f"Failed to update component specifications: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update specifications: {str(e)}",
        )


@router.get(
    "/components/{component_id}/bindings", response_model=List[ComponentBindingResponse]
)
async def get_component_bindings(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all document bindings for a component.
    """
    try:
        component = (
            db.query(models.Component)
            .filter(
                and_(
                    models.Component.id == uuid.UUID(component_id),
                    models.Component.tenant_id == current_user["tenant_id"],
                )
            )
            .first()
        )

        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
            )

        bindings = []
        if component.management and component.management.media:
            doc_bindings = component.management.media.get("doc_bindings", {}).get(
                "bindings", []
            )

            for binding in doc_bindings:
                bindings.append(
                    ComponentBindingResponse(
                        id=binding.get("id", ""),
                        component_id=component_id,
                        document_id=binding.get("document_id", ""),
                        binding_type=binding.get("binding_type", ""),
                        location_path=binding.get("location_path", ""),
                        metadata=binding.get("metadata"),
                        created_at=datetime.fromisoformat(
                            binding.get("created_at", datetime.utcnow().isoformat())
                        ),
                    )
                )

        return bindings

    except Exception as e:
        logger.error(f"Failed to get component bindings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bindings: {str(e)}",
        )


# Helper Functions


def create_component_reference(
    component: models.Component, binding_type: str, metadata: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create a component reference for ODL-SD document."""
    base_ref = {
        "component_id": component.component_id,
        "name": component.name,
        "brand": component.brand,
        "part_number": component.part_number,
        "rating_w": component.rating_w,
        "category": component.category,
        "subcategory": component.subcategory,
        "domain": component.domain,
        "scale": component.scale,
    }

    if binding_type == "library":
        # Library reference includes full component definition
        base_ref.update(
            {
                "status": component.status,
                "classification": component.classification,
                "is_active": component.is_active,
            }
        )
    elif binding_type == "instance":
        # Instance reference includes placement and configuration
        base_ref.update(
            {
                "instance_id": f"INST-{uuid.uuid4().hex[:8].upper()}",
                "placement": metadata.get("placement", {}),
                "configuration": metadata.get("configuration", {}),
            }
        )
    elif binding_type == "specification":
        # Specification reference includes technical specs
        base_ref.update({"specifications": metadata.get("specifications", {})})

    return base_ref


def create_component_binding_patch(
    odl_document: OdlDocument,
    component_ref: Dict[str, Any],
    location_path: str,
    binding_type: str,
) -> List[Dict[str, Any]]:
    """Create JSON patch operations for component binding."""
    patches = []

    # Ensure the target path exists
    path_parts = location_path.split(".")
    current_path = ""

    for i, part in enumerate(path_parts):
        if current_path:
            current_path += f".{part}"
        else:
            current_path = part

        # Check if path exists and create if needed
        if i == len(path_parts) - 1:
            # Final path - add the component
            patches.append(
                {
                    "op": "add",
                    "path": f"/{current_path.replace('.', '/')}/0",
                    "value": component_ref,
                }
            )
        else:
            # Intermediate path - ensure object exists
            patches.append(
                {
                    "op": "test",
                    "path": f"/{current_path.replace('.', '/')}",
                    "value": None,
                }
            )

    return patches


def create_odl_component_instance(
    component: models.Component, instance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create ODL-SD component instance from component and instance data."""
    instance = {
        "component_id": component.component_id,
        "name": component.name,
        "brand": component.brand,
        "part_number": component.part_number,
        "rating_w": component.rating_w,
        "category": component.category,
        "subcategory": component.subcategory,
        "domain": component.domain,
        "scale": component.scale,
        "instance_id": instance_data.get(
            "instance_id", f"INST-{uuid.uuid4().hex[:8].upper()}"
        ),
        "quantity": instance_data.get("quantity", 1),
        "placement": instance_data.get("placement", {}),
        "configuration": instance_data.get("configuration", {}),
        "connections": instance_data.get("connections", []),
        "status": "planned",
    }

    # Add component management if available
    if component.management:
        instance["component_management"] = {
            "version": component.management.version,
            "tracking_policy": component.management.tracking_policy,
            "traceability": component.management.traceability,
        }

    return instance


def update_component_specs_in_document(
    odl_document: OdlDocument,
    component_id: str,
    specifications: Dict[str, Any],
    merge_strategy: str,
) -> bool:
    """Update component specifications in ODL-SD document."""
    updated = False

    # Search for component instances in the document
    if hasattr(odl_document, "libraries") and odl_document.libraries:
        components = odl_document.libraries.get("components", [])

        for i, comp in enumerate(components):
            if comp.get("component_id") == component_id:
                if merge_strategy == "deep_merge":
                    # Deep merge specifications
                    if "specifications" not in comp:
                        comp["specifications"] = {}
                    deep_merge_dict(comp["specifications"], specifications)
                else:
                    # Replace specifications
                    comp["specifications"] = specifications

                updated = True

    return updated


def deep_merge_dict(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge_dict(target[key], value)
        else:
            target[key] = value
    return target
