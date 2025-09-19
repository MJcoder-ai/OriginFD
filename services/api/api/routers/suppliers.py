"""
Supplier management API endpoints.
Handles supplier onboarding, management, and component sourcing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import models
from core.auth import get_current_user
from core.database import SessionDep
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models


class SupplierCreateRequest(BaseModel):
    """Request model for creating suppliers."""

    name: str = Field(..., min_length=1, max_length=120)
    gln: Optional[str] = Field(
        None, pattern=r"^\d{13}$", description="GS1 Global Location Number"
    )
    contact: Dict[str, Any] = Field(..., description="Contact information")
    capabilities: Optional[Dict[str, Any]] = Field(
        None, description="Supplier capabilities"
    )
    certifications: Optional[Dict[str, Any]] = Field(
        None, description="Quality certifications"
    )


class SupplierUpdateRequest(BaseModel):
    """Request model for updating suppliers."""

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    gln: Optional[str] = Field(None, pattern=r"^\d{13}$")
    contact: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None
    status: Optional[models.SupplierStatusEnum] = None


class SupplierResponse(BaseModel):
    """Response model for supplier data."""

    id: str
    supplier_id: str
    name: str
    gln: Optional[str]
    contact: Dict[str, Any]
    status: str
    capabilities: Optional[Dict[str, Any]]
    certifications: Optional[Dict[str, Any]]
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    """Response model for supplier listings."""

    suppliers: List[SupplierResponse]
    total: int
    page: int
    page_size: int


class RFQCreateRequest(BaseModel):
    """Request model for creating RFQs."""

    lines: List[Dict[str, Any]] = Field(..., description="RFQ line items")
    deadline: Optional[datetime] = Field(None, description="Response deadline")
    evaluation: Optional[Dict[str, Any]] = Field(
        None, description="Evaluation criteria"
    )


class RFQResponse(BaseModel):
    """Response model for RFQ data."""

    id: str
    rfq_id: str
    status: str
    round: int
    deadline: Optional[datetime]
    issued_at: Optional[datetime]
    awarded_at: Optional[datetime]
    lines: List[Dict[str, Any]]
    bids: Optional[List[Dict[str, Any]]]
    evaluation: Optional[Dict[str, Any]]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Supplier CRUD Operations


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    request: SupplierCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new supplier.
    """
    try:
        # Generate supplier ID
        supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"

        # Check for duplicate names
        existing = (
            db.query(models.Supplier)
            .filter(
                and_(
                    models.Supplier.tenant_id == current_user["tenant_id"],
                    models.Supplier.name == request.name,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Supplier with this name already exists",
            )

        # Validate contact information
        if not request.contact.get("email") and not request.contact.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier must have at least email or phone contact",
            )

        # Create supplier
        supplier = models.Supplier(
            tenant_id=uuid.UUID(current_user["tenant_id"]),
            supplier_id=supplier_id,
            name=request.name,
            gln=request.gln,
            contact=request.contact,
            status=models.SupplierStatusEnum.DRAFT,
            capabilities=request.capabilities or {},
            certifications=request.certifications or {},
            created_by=uuid.UUID(current_user["id"]),
        )

        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        logger.info(
            f"Created supplier {supplier.supplier_id} by user {current_user['id']}"
        )

        return SupplierResponse(
            id=str(supplier.id),
            supplier_id=supplier.supplier_id,
            name=supplier.name,
            gln=supplier.gln,
            contact=supplier.contact,
            status=supplier.status,
            capabilities=supplier.capabilities,
            certifications=supplier.certifications,
            approved_at=supplier.approved_at,
            approved_by=str(supplier.approved_by) if supplier.approved_by else None,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at,
            created_by=str(supplier.created_by) if supplier.created_by else None,
        )

    except Exception as e:
        logger.error(f"Failed to create supplier: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create supplier: {str(e)}",
        )


@router.get("/", response_model=SupplierListResponse)
async def list_suppliers(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[models.SupplierStatusEnum] = None,
    search: Optional[str] = None,
    capabilities: Optional[str] = None,
):
    """
    List suppliers with filtering and pagination.
    """
    query = db.query(models.Supplier).filter(
        models.Supplier.tenant_id == current_user["tenant_id"]
    )

    # Apply filters
    if status:
        query = query.filter(models.Supplier.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Supplier.name.ilike(search_term),
                models.Supplier.supplier_id.ilike(search_term),
            )
        )

    if capabilities:
        # Search in capabilities JSON
        query = query.filter(models.Supplier.capabilities.op("?")(capabilities))

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    suppliers = (
        query.order_by(models.Supplier.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert to response models
    supplier_responses = []
    for supplier in suppliers:
        supplier_responses.append(
            SupplierResponse(
                id=str(supplier.id),
                supplier_id=supplier.supplier_id,
                name=supplier.name,
                gln=supplier.gln,
                contact=supplier.contact,
                status=supplier.status,
                capabilities=supplier.capabilities,
                certifications=supplier.certifications,
                approved_at=supplier.approved_at,
                approved_by=str(supplier.approved_by) if supplier.approved_by else None,
                created_at=supplier.created_at,
                updated_at=supplier.updated_at,
                created_by=str(supplier.created_by) if supplier.created_by else None,
            )
        )

    return SupplierListResponse(
        suppliers=supplier_responses, total=total, page=page, page_size=page_size
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific supplier by ID.
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid supplier ID format"
        )

    supplier = (
        db.query(models.Supplier)
        .filter(
            and_(
                models.Supplier.id == supplier_uuid,
                models.Supplier.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )

    return SupplierResponse(
        id=str(supplier.id),
        supplier_id=supplier.supplier_id,
        name=supplier.name,
        gln=supplier.gln,
        contact=supplier.contact,
        status=supplier.status,
        capabilities=supplier.capabilities,
        certifications=supplier.certifications,
        approved_at=supplier.approved_at,
        approved_by=str(supplier.approved_by) if supplier.approved_by else None,
        created_at=supplier.created_at,
        updated_at=supplier.updated_at,
        created_by=str(supplier.created_by) if supplier.created_by else None,
    )


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    request: SupplierUpdateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a supplier.
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid supplier ID format"
        )

    supplier = (
        db.query(models.Supplier)
        .filter(
            and_(
                models.Supplier.id == supplier_uuid,
                models.Supplier.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )

    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value == models.SupplierStatusEnum.APPROVED:
            # Set approval timestamp and user
            supplier.approved_at = datetime.utcnow()
            supplier.approved_by = uuid.UUID(current_user["id"])

        setattr(supplier, field, value)

    supplier.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(supplier)

    logger.info(f"Updated supplier {supplier.supplier_id} by user {current_user['id']}")

    return SupplierResponse(
        id=str(supplier.id),
        supplier_id=supplier.supplier_id,
        name=supplier.name,
        gln=supplier.gln,
        contact=supplier.contact,
        status=supplier.status,
        capabilities=supplier.capabilities,
        certifications=supplier.certifications,
        approved_at=supplier.approved_at,
        approved_by=str(supplier.approved_by) if supplier.approved_by else None,
        created_at=supplier.created_at,
        updated_at=supplier.updated_at,
        created_by=str(supplier.created_by) if supplier.created_by else None,
    )


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Deactivate a supplier (soft delete).
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid supplier ID format"
        )

    supplier = (
        db.query(models.Supplier)
        .filter(
            and_(
                models.Supplier.id == supplier_uuid,
                models.Supplier.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )

    # Deactivate instead of hard delete
    supplier.status = models.SupplierStatusEnum.INACTIVE
    supplier.updated_at = datetime.utcnow()

    db.commit()

    logger.info(
        f"Deactivated supplier {supplier.supplier_id} by user {current_user['id']}"
    )

    return {"message": "Supplier deactivated successfully"}


# RFQ Management


@router.post("/rfqs", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
async def create_rfq(
    request: RFQCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new Request for Quotation.
    """
    try:
        # Generate RFQ ID
        rfq_id = f"RFQ-{uuid.uuid4().hex[:8].upper()}"

        # Create RFQ
        rfq = models.RFQ(
            tenant_id=uuid.UUID(current_user["tenant_id"]),
            rfq_id=rfq_id,
            status=models.RFQStatusEnum.DRAFT,
            round=1,
            deadline=request.deadline,
            lines=request.lines,
            bids=[],
            evaluation=request.evaluation or {},
            created_by=uuid.UUID(current_user["id"]),
        )

        db.add(rfq)
        db.commit()
        db.refresh(rfq)

        logger.info(f"Created RFQ {rfq.rfq_id} by user {current_user['id']}")

        return RFQResponse(
            id=str(rfq.id),
            rfq_id=rfq.rfq_id,
            status=rfq.status,
            round=rfq.round,
            deadline=rfq.deadline,
            issued_at=rfq.issued_at,
            awarded_at=rfq.awarded_at,
            lines=rfq.lines,
            bids=rfq.bids,
            evaluation=rfq.evaluation,
            created_by=str(rfq.created_by),
            created_at=rfq.created_at,
            updated_at=rfq.updated_at,
        )

    except Exception as e:
        logger.error(f"Failed to create RFQ: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create RFQ: {str(e)}",
        )


@router.get("/rfqs", response_model=List[RFQResponse])
async def list_rfqs(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    status: Optional[models.RFQStatusEnum] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List RFQs with filtering and pagination.
    """
    query = db.query(models.RFQ).filter(
        models.RFQ.tenant_id == current_user["tenant_id"]
    )

    if status:
        query = query.filter(models.RFQ.status == status)

    rfqs = (
        query.order_by(models.RFQ.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return [
        RFQResponse(
            id=str(rfq.id),
            rfq_id=rfq.rfq_id,
            status=rfq.status,
            round=rfq.round,
            deadline=rfq.deadline,
            issued_at=rfq.issued_at,
            awarded_at=rfq.awarded_at,
            lines=rfq.lines,
            bids=rfq.bids,
            evaluation=rfq.evaluation,
            created_by=str(rfq.created_by),
            created_at=rfq.created_at,
            updated_at=rfq.updated_at,
        )
        for rfq in rfqs
    ]


@router.post("/{supplier_id}/approve")
async def approve_supplier(
    supplier_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Approve a supplier for sourcing.
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid supplier ID format"
        )

    supplier = (
        db.query(models.Supplier)
        .filter(
            and_(
                models.Supplier.id == supplier_uuid,
                models.Supplier.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )

    if supplier.status == models.SupplierStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier is already approved",
        )

    # Approve supplier
    supplier.status = models.SupplierStatusEnum.APPROVED
    supplier.approved_at = datetime.utcnow()
    supplier.approved_by = uuid.UUID(current_user["id"])
    supplier.updated_at = datetime.utcnow()

    db.commit()

    logger.info(
        f"Approved supplier {supplier.supplier_id} by user {current_user['id']}"
    )

    return {"message": "Supplier approved successfully"}


@router.get("/stats/summary")
async def get_supplier_stats(
    db: Session = Depends(SessionDep), current_user: dict = Depends(get_current_user)
):
    """
    Get supplier statistics for dashboard.
    """
    tenant_id = current_user["tenant_id"]

    # Total suppliers
    total_suppliers = (
        db.query(models.Supplier).filter(models.Supplier.tenant_id == tenant_id).count()
    )

    # Approved suppliers
    approved_suppliers = (
        db.query(models.Supplier)
        .filter(
            and_(
                models.Supplier.tenant_id == tenant_id,
                models.Supplier.status == models.SupplierStatusEnum.APPROVED,
            )
        )
        .count()
    )

    # Draft suppliers
    draft_suppliers = (
        db.query(models.Supplier)
        .filter(
            and_(
                models.Supplier.tenant_id == tenant_id,
                models.Supplier.status == models.SupplierStatusEnum.DRAFT,
            )
        )
        .count()
    )

    # Active RFQs
    active_rfqs = (
        db.query(models.RFQ)
        .filter(
            and_(
                models.RFQ.tenant_id == tenant_id,
                models.RFQ.status.in_(
                    [
                        models.RFQStatusEnum.ISSUED,
                        models.RFQStatusEnum.BIDDING,
                        models.RFQStatusEnum.EVALUATING,
                    ]
                ),
            )
        )
        .count()
    )

    return {
        "total_suppliers": total_suppliers,
        "approved_suppliers": approved_suppliers,
        "draft_suppliers": draft_suppliers,
        "active_rfqs": active_rfqs,
    }
