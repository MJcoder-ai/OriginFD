"""
ODL-SD document management endpoints with JSON-Patch support.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# from core.rbac import guard_patch, has_document_access  # TODO: Implement RBAC
import models
from deps import get_current_user
from core.database import SessionDep
from fastapi import APIRouter, Depends, HTTPException, Query, status
from odl_sd.schemas import OdlSdDocument
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from odl_sd_patch import apply_patch, inverse_patch, PatchValidationError

router = APIRouter()


class DocumentCreateRequest(BaseModel):
    """Request model for creating new documents."""

    project_name: str = Field(..., min_length=1, max_length=255)
    portfolio_id: Optional[str] = None
    domain: str = Field(..., pattern="^(PV|BESS|HYBRID|GRID|MICROGRID)$")
    scale: str = Field(
        ..., pattern="^(RESIDENTIAL|COMMERCIAL|INDUSTRIAL|UTILITY|HYPERSCALE)$"
    )
    document_data: Dict[str, Any]


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    id: str
    project_name: str
    domain: str
    scale: str
    current_version: int
    content_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PatchRequest(BaseModel):
    """Request model for JSON-Patch operations."""

    doc_id: str
    doc_version: int
    patch: List[Dict[str, Any]] = Field(..., max_items=100)
    evidence: List[str] = Field(default_factory=list)
    dry_run: bool = False
    change_summary: Optional[str] = None


class PatchResponse(BaseModel):
    """Response model for patch operations."""

    success: bool
    doc_version: int
    content_hash: str
    inverse_patch: List[Dict[str, Any]]
    applied_at: datetime


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new ODL-SD document.
    """
    try:
        # Validate ODL-SD document structure
        odl_doc = OdlSdDocument.parse_obj(request.document_data)
        validation_result = odl_doc.validate_document()

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ODL-SD document: {validation_result.errors}",
            )

        # Create database record
        document = models.Document(
            tenant_id=uuid.UUID(current_user["tenant_id"]),  # From JWT
            project_name=request.project_name,
            portfolio_id=(
                uuid.UUID(request.portfolio_id) if request.portfolio_id else None
            ),
            domain=request.domain,
            scale=request.scale,
            current_version=1,
            content_hash=odl_doc.meta.versioning.content_hash,
            document_data=request.document_data,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Create initial version record
        version = models.DocumentVersion(
            tenant_id=document.tenant_id,
            document_id=document.id,
            version_number=1,
            content_hash=document.content_hash,
            created_by=uuid.UUID(current_user["id"]),
            document_data=request.document_data,
        )

        db.add(version)
        db.commit()

        return DocumentResponse(
            id=str(document.id),
            project_name=document.project_name,
            domain=document.domain,
            scale=document.scale,
            current_version=document.current_version,
            content_hash=document.content_hash,
            is_active=document.is_active,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{doc_id}", response_model=Dict[str, Any])
async def get_document(
    doc_id: str,
    version: Optional[int] = Query(None, description="Specific version number"),
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get ODL-SD document by ID, optionally at specific version.
    """
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    # Get document
    document = (
        db.query(models.Document)
        .filter(
            models.Document.id == doc_uuid,
            models.Document.tenant_id == uuid.UUID(current_user["tenant_id"]),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # TODO: Check document access permissions
    # if not has_document_access(current_user, document, "read"):
    #     raise HTTPException(status_code=403, detail="Access denied")

    if version is None:
        # Return current version
        return document.document_data
    else:
        # Return specific version
        doc_version = (
            db.query(models.DocumentVersion)
            .filter(
                models.DocumentVersion.document_id == doc_uuid,
                models.DocumentVersion.version_number == version,
                models.DocumentVersion.tenant_id
                == uuid.UUID(current_user["tenant_id"]),
            )
            .first()
        )

        if not doc_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found",
            )

        return doc_version.document_data


@router.post("/patch", response_model=PatchResponse)
async def apply_document_patch(
    request: PatchRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Apply JSON-Patch operations to an ODL-SD document.
    This is the core write endpoint - all document mutations go through here.
    """
    try:
        doc_uuid = uuid.UUID(request.doc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    # Get current document with row lock
    document = (
        db.query(models.Document)
        .filter(
            models.Document.id == doc_uuid,
            models.Document.tenant_id == uuid.UUID(current_user["tenant_id"]),
        )
        .with_for_update()
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Version conflict check (optimistic concurrency)
    if document.current_version != request.doc_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version conflict. Expected {request.doc_version}, got {document.current_version}",
        )

    # TODO: RBAC and phase gate checks
    # guard_patch(
    #     user=current_user,
    #     doc_id=request.doc_id,
    #     patch=request.patch,
    #     db=db
    # )

    try:
        # Generate inverse patch before applying changes
        inverse_ops = inverse_patch(request.patch, document.document_data)

        # Apply patch
        patched_doc = apply_patch(
            document.document_data,
            request.patch,
            evidence=request.evidence,
            dry_run=request.dry_run,
            actor=current_user["id"],
        )

        if request.dry_run:
            # Return preview without saving
            return PatchResponse(
                success=True,
                doc_version=document.current_version,
                content_hash=document.content_hash,
                inverse_patch=inverse_ops,
                applied_at=datetime.utcnow(),
            )

        # Validate patched document
        odl_doc = OdlSdDocument.parse_obj(patched_doc)
        validation_result = odl_doc.validate_document()

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patched document invalid: {validation_result.errors}",
            )

        # Update database
        new_version = document.current_version + 1
        old_hash = document.content_hash
        new_hash = odl_doc.meta.versioning.content_hash

        # Update document record
        document.current_version = new_version
        document.content_hash = new_hash
        document.document_data = patched_doc
        document.updated_at = datetime.utcnow()

        # Create version record
        version = models.DocumentVersion(
            tenant_id=document.tenant_id,
            document_id=document.id,
            version_number=new_version,
            content_hash=new_hash,
            previous_hash=old_hash,
            change_summary=request.change_summary,
            patch_operations=request.patch,
            evidence_uris=request.evidence,
            created_by=uuid.UUID(current_user["id"]),
            document_data=patched_doc,
        )

        db.add(version)
        db.commit()

        return PatchResponse(
            success=True,
            doc_version=new_version,
            content_hash=new_hash,
            inverse_patch=inverse_ops,
            applied_at=datetime.utcnow(),
        )

    except PatchValidationError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patch validation failed: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patch application failed: {str(e)}",
        )


@router.get("/{doc_id}/versions")
async def get_document_versions(
    doc_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get version history for a document.
    """
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    # Check document exists and user has access
    document = (
        db.query(models.Document)
        .filter(
            models.Document.id == doc_uuid,
            models.Document.tenant_id == uuid.UUID(current_user["tenant_id"]),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Get versions
    versions = (
        db.query(models.DocumentVersion)
        .filter(
            models.DocumentVersion.document_id == doc_uuid,
            models.DocumentVersion.tenant_id == uuid.UUID(current_user["tenant_id"]),
        )
        .order_by(models.DocumentVersion.version_number.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "version_number": v.version_number,
            "content_hash": v.content_hash,
            "change_summary": v.change_summary,
            "created_by": str(v.created_by),
            "created_at": v.created_at,
            "patch_operations_count": len(v.patch_operations or []),
        }
        for v in versions
    ]


@router.get("/{doc_id}/audit")
async def get_document_audit_trail(
    doc_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get complete audit trail for a document.
    """
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    document = (
        db.query(models.Document)
        .filter(
            models.Document.id == doc_uuid,
            models.Document.tenant_id == uuid.UUID(current_user["tenant_id"]),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Extract audit trail from document
    audit_trail = document.document_data.get("audit", [])

    return {
        "document_id": doc_id,
        "total_entries": len(audit_trail),
        "audit_entries": audit_trail,
    }
