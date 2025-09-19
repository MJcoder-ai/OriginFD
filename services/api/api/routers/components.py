"""
Component management API endpoints.
Implements ODL-SD v4.1 Component Management lifecycle.
"""

import logging
import uuid
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import models
from api.routers.auth import get_current_user
from core.database import SessionDep
from core.performance import cached_response
from core.performance import invalidate_component_cache
from core.performance import monitor_performance
from core.performance import performance_metrics
from core.performance import rate_limit
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import Query
from fastapi import UploadFile
from fastapi import status
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models


class ComponentCreateRequest(BaseModel):
    """Request model for creating new components."""

    brand: str = Field(..., min_length=1, max_length=64)
    part_number: str = Field(..., min_length=1, max_length=64)
    rating_w: int = Field(..., ge=1, le=1000000)
    category: Optional[str] = Field(None, max_length=50)
    subcategory: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=20)
    scale: Optional[str] = Field(None, max_length=20)
    classification: Optional[Dict[str, Any]] = None
    warranty_status: Optional[str] = Field("inactive", max_length=50)
    rma_tracking: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        extra = "forbid"  # Prevent mass assignment vulnerabilities


class ComponentUpdateRequest(BaseModel):
    """Request model for updating components."""

    brand: Optional[str] = Field(None, min_length=1, max_length=64)
    part_number: Optional[str] = Field(None, min_length=1, max_length=64)
    rating_w: Optional[int] = Field(None, ge=1, le=1000000)
    category: Optional[str] = Field(None, max_length=50)
    subcategory: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=20)
    scale: Optional[str] = Field(None, max_length=20)
    classification: Optional[Dict[str, Any]] = None
    warranty_status: Optional[str] = Field(None, max_length=50)
    rma_tracking: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "forbid"  # Prevent mass assignment vulnerabilities


class ComponentResponse(BaseModel):
    """Response model for component data."""

    id: str
    component_id: str
    brand: str
    part_number: str
    rating_w: int
    name: str
    status: str
    category: Optional[str]
    subcategory: Optional[str]
    domain: Optional[str]
    scale: Optional[str]
    classification: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    warranty_status: Optional[str]
    rma_tracking: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class ComponentListResponse(BaseModel):
    """Response model for component listings."""

    components: List[ComponentResponse]
    total: int
    page: int
    page_size: int


class ComponentStatusTransitionRequest(BaseModel):
    """Request model for status transitions."""

    new_status: models.ComponentStatusEnum
    comment: Optional[str] = None


class DatasheetUploadRequest(BaseModel):
    """Request model for datasheet upload."""

    datasheet_url: str
    extract_images: bool = True
    ai_parse: bool = True


class MediaAssetResponse(BaseModel):
    """Response model for media assets."""

    id: str
    asset_id: str
    type: str
    scope: str
    uri: str
    hash: str
    mime: Optional[str]
    width_px: Optional[int]
    height_px: Optional[int]
    alt_text: Optional[str]
    approved_for_external: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Component CRUD Operations


@router.post("/", response_model=ComponentResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)  # More restrictive for write operations
@performance_metrics
async def create_component(
    request: ComponentCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new component in draft status.
    """
    try:
        # Generate component ID and name
        component_id = (
            f"CMP:{request.brand}:{request.part_number}:{request.rating_w}W:REV1"
        )
        name = f"{request.brand}_{request.part_number}_{request.rating_w}W"

        # Check for duplicates
        existing = (
            db.query(models.Component)
            .filter(or_(models.Component.component_id == component_id, models.Component.name == name))
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Component with this ID or name already exists",
            )

        # Create component
        component = models.Component(
            tenant_id=uuid.UUID(current_user["tenant_id"]),
            component_id=component_id,
            brand=request.brand,
            part_number=request.part_number,
            rating_w=request.rating_w,
            name=name,
            status=models.ComponentStatusEnum.DRAFT,
            category=request.category,
            subcategory=request.subcategory,
            domain=request.domain,
            scale=request.scale,
            classification=request.classification,
            created_by=uuid.UUID(current_user["id"]),
        )

        if hasattr(component, "warranty_status"):
            component.warranty_status = request.warranty_status
        if hasattr(component, "rma_tracking"):
            component.rma_tracking = request.rma_tracking or []

        db.add(component)
        db.flush()  # Get the component ID

        # Create component management record
        management = models.ComponentManagement(
            component_id=component.id,
            version="1.0",
            tracking_policy={"level": "quantity"},  # Default tracking
            approvals={"requested": False, "records": []},
            supplier_chain={"suppliers": []},
            order_management={"rfq_enabled": True, "orders": [], "shipments": []},
            inventory={"stocks": []},
            warranty={"terms": {}, "claims": []},
            returns={"policies": {}, "records": []},
            traceability={},
            compliance={"standards": [], "certificates": []},
            ai_logs=[],
            audit=[],
            analytics={"kpis": {}},
            media={
                "library": [],
                "capture_policy": {},
                "doc_bindings": {"bindings": []},
            },
        )

        db.add(management)
        db.commit()
        db.refresh(component)

        # Invalidate related cache entries
        await invalidate_component_cache()

        logger.info(
            f"Created component {component.component_id} by user {current_user['id']}"
        )

        return ComponentResponse(
            id=str(component.id),
            component_id=component.component_id,
            brand=component.brand,
            part_number=component.part_number,
            rating_w=component.rating_w,
            name=component.name,
            status=component.status,
            category=component.category,
            subcategory=component.subcategory,
            domain=component.domain,
            scale=component.scale,
            classification=component.classification,
            is_active=component.is_active,
            created_at=component.created_at,
            updated_at=component.updated_at,
            created_by=str(component.created_by) if component.created_by else None,
            warranty_status=getattr(
                component, "warranty_status", request.warranty_status
            ),
            rma_tracking=getattr(component, "rma_tracking", request.rma_tracking or []),
        )

    except Exception as e:
        logger.error(f"Failed to create component: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create component: {str(e)}",
        )


@router.get("/", response_model=ComponentListResponse)
@cached_response(ttl=300, include_user=True)
@rate_limit(requests_per_minute=100)
@performance_metrics
async def list_components(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[models.ComponentStatusEnum] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = Query(False),
):
    """
    List components with filtering and pagination.
    """
    # Use eager loading to prevent N+1 queries when accessing relationships
    from sqlalchemy.orm import joinedload
    from sqlalchemy.orm import selectinload

    query = (
        db.query(models.Component)
        .options(
            # Eager load commonly accessed relationships to prevent N+1 queries
            joinedload(models.Component.supplier),
            selectinload(models.Component.inventory_records),
            # Add more relationships as they're defined in the model
        )
        .filter(models.Component.tenant_id == current_user["tenant_id"])
    )

    # Apply filters
    if status:
        query = query.filter(models.Component.status == status)

    if category:
        query = query.filter(models.Component.category == category)

    if domain:
        query = query.filter(models.Component.domain == domain)

    if brand:
        query = query.filter(models.Component.brand.ilike(f"%{brand}%"))

    if active_only:
        active_states = [
            models.ComponentStatusEnum.APPROVED,
            models.ComponentStatusEnum.AVAILABLE,
            models.ComponentStatusEnum.RFQ_OPEN,
            models.ComponentStatusEnum.RFQ_AWARDED,
            models.ComponentStatusEnum.PURCHASING,
            models.ComponentStatusEnum.ORDERED,
            models.ComponentStatusEnum.SHIPPED,
            models.ComponentStatusEnum.RECEIVED,
            models.ComponentStatusEnum.INSTALLED,
            models.ComponentStatusEnum.COMMISSIONED,
            models.ComponentStatusEnum.OPERATIONAL,
            models.ComponentStatusEnum.WARRANTY_ACTIVE,
        ]
        query = query.filter(models.Component.status.in_([s.value for s in active_states]))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Component.name.ilike(search_term),
                models.Component.brand.ilike(search_term),
                models.Component.part_number.ilike(search_term),
                models.Component.component_id.ilike(search_term),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    components = (
        query.order_by(models.Component.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert to response models
    component_responses = []
    for comp in components:
        component_responses.append(
            ComponentResponse(
                id=str(comp.id),
                component_id=comp.component_id,
                brand=comp.brand,
                part_number=comp.part_number,
                rating_w=comp.rating_w,
                name=comp.name,
                status=comp.status,
                category=comp.category,
                subcategory=comp.subcategory,
                domain=comp.domain,
                scale=comp.scale,
                classification=comp.classification,
                is_active=comp.is_active,
                created_at=comp.created_at,
                updated_at=comp.updated_at,
                created_by=str(comp.created_by) if comp.created_by else None,
                warranty_status=getattr(comp, "warranty_status", None),
                rma_tracking=getattr(comp, "rma_tracking", []),
            )
        )

    return ComponentListResponse(
        components=component_responses, total=total, page=page, page_size=page_size
    )


@router.get("/{component_id}", response_model=ComponentResponse)
@cached_response(ttl=600, include_user=True)
@rate_limit(requests_per_minute=200)
@performance_metrics
async def get_component(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific component by ID.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format",
        )

    component = (
        db.query(models.Component)
        .filter(
            and_(
                models.Component.id == component_uuid,
                models.Component.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
        )

    return ComponentResponse(
        id=str(component.id),
        component_id=component.component_id,
        brand=component.brand,
        part_number=component.part_number,
        rating_w=component.rating_w,
        name=component.name,
        status=component.status,
        category=component.category,
        subcategory=component.subcategory,
        domain=component.domain,
        scale=component.scale,
        classification=component.classification,
        is_active=component.is_active,
        created_at=component.created_at,
        updated_at=component.updated_at,
        created_by=str(component.created_by) if component.created_by else None,
        warranty_status=getattr(component, "warranty_status", None),
        rma_tracking=getattr(component, "rma_tracking", []),
    )


@router.patch("/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: str,
    request: ComponentUpdateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a component.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format",
        )

    component = (
        db.query(models.Component)
        .filter(
            and_(
                models.Component.id == component_uuid,
                models.Component.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
        )

    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field in ["brand", "part_number", "rating_w"] and value is not None:
            # If core identity fields change, regenerate component_id and name
            setattr(component, field, value)

    # Regenerate component_id and name if identity fields changed
    if any(field in update_data for field in ["brand", "part_number", "rating_w"]):
        component.component_id = (
            f"CMP:{component.brand}:{component.part_number}:{component.rating_w}W:REV1"
        )
        component.name = (
            f"{component.brand}_{component.part_number}_{component.rating_w}W"
        )

    # Update other fields
    for field, value in update_data.items():
        if field not in ["brand", "part_number", "rating_w"] and hasattr(
            component, field
        ):
            setattr(component, field, value)

    component.updated_by = uuid.UUID(current_user["id"])
    component.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(component)

    # Invalidate related cache entries
    await invalidate_component_cache(str(component.id))

    logger.info(
        f"Updated component {component.component_id} by user {current_user['id']}"
    )

    return ComponentResponse(
        id=str(component.id),
        component_id=component.component_id,
        brand=component.brand,
        part_number=component.part_number,
        rating_w=component.rating_w,
        name=component.name,
        status=component.status,
        category=component.category,
        subcategory=component.subcategory,
        domain=component.domain,
        scale=component.scale,
        classification=component.classification,
        is_active=component.is_active,
        created_at=component.created_at,
        updated_at=component.updated_at,
        created_by=str(component.created_by) if component.created_by else None,
        warranty_status=getattr(component, "warranty_status", None),
        rma_tracking=getattr(component, "rma_tracking", []),
    )


@router.delete("/{component_id}")
async def delete_component(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Archive a component (soft delete).
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format",
        )

    component = (
        db.query(models.Component)
        .filter(
            and_(
                models.Component.id == component_uuid,
                models.Component.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
        )

    # Archive instead of hard delete
    component.status = models.ComponentStatusEnum.ARCHIVED
    component.updated_by = uuid.UUID(current_user["id"])
    component.updated_at = datetime.utcnow()

    db.commit()

    # Invalidate related cache entries
    await invalidate_component_cache(str(component.id))

    logger.info(
        f"Archived component {component.component_id} by user {current_user['id']}"
    )

    return {"message": "Component archived successfully"}


# Component Status Transitions


@router.post("/{component_id}/transition", response_model=ComponentResponse)
async def transition_component_status(
    component_id: str,
    request: ComponentStatusTransitionRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Transition component status with validation.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format",
        )

    component = (
        db.query(models.Component)
        .filter(
            and_(
                models.Component.id == component_uuid,
                models.Component.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
        )

    # Validate transition
    if not component.can_transition_to(request.new_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {component.status} to {request.new_status.value}",
        )

    old_status = component.status
    component.status = request.new_status.value
    component.updated_by = uuid.UUID(current_user["id"])
    component.updated_at = datetime.utcnow()

    # Add audit record to component management
    if component.management:
        component.management.add_audit_record(
            action=f"status_transition",
            actor_role="engineer",  # TODO: Get from user roles
            actor=current_user["email"],
            diff=f"Status changed from {old_status} to {request.new_status.value}",
        )

    db.commit()
    db.refresh(component)

    # Invalidate related cache entries
    await invalidate_component_cache(str(component.id))

    logger.info(
        f"Transitioned component {component.component_id} from {old_status} to {request.new_status.value}"
    )

    return ComponentResponse(
        id=str(component.id),
        component_id=component.component_id,
        brand=component.brand,
        part_number=component.part_number,
        rating_w=component.rating_w,
        name=component.name,
        status=component.status,
        category=component.category,
        subcategory=component.subcategory,
        domain=component.domain,
        scale=component.scale,
        classification=component.classification,
        is_active=component.is_active,
        created_at=component.created_at,
        updated_at=component.updated_at,
        created_by=str(component.created_by) if component.created_by else None,
        warranty_status=getattr(component, "warranty_status", None),
        rma_tracking=getattr(component, "rma_tracking", []),
    )


# Media Management


@router.get("/{component_id}/media", response_model=List[MediaAssetResponse])
async def list_component_media(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    asset_type: Optional[models.MediaAssetTypeEnum] = None,
):
    """
    List media assets for a component.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format",
        )

    # Verify component exists and user has access
    component = (
        db.query(models.Component)
        .filter(
            and_(
                models.Component.id == component_uuid,
                models.Component.tenant_id == current_user["tenant_id"],
            )
        )
        .first()
    )

    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Component not found"
        )

    query = db.query(models.MediaAsset).filter(models.MediaAsset.component_id == component_uuid)

    if asset_type:
        query = query.filter(models.MediaAsset.type == asset_type.value)

    media_assets = query.order_by(models.MediaAsset.created_at.desc()).all()

    return [
        MediaAssetResponse(
            id=str(asset.id),
            asset_id=asset.asset_id,
            type=asset.type,
            scope=asset.scope,
            uri=asset.uri,
            hash=asset.hash,
            mime=asset.mime,
            width_px=asset.width_px,
            height_px=asset.height_px,
            alt_text=asset.alt_text,
            approved_for_external=asset.approved_for_external,
            created_at=asset.created_at,
        )
        for asset in media_assets
    ]


@router.post("/{component_id}/media/upload")
async def upload_component_media(
    component_id: str,
    file: UploadFile = File(...),
    asset_type: models.MediaAssetTypeEnum = models.MediaAssetTypeEnum.COMPONENT_PHOTO_HERO,
    scope: models.MediaScopeEnum = models.MediaScopeEnum.COMPONENT_GENERIC,
    alt_text: Optional[str] = None,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload media asset for a component.
    """
    # TODO: Implement file upload to storage (S3, GCS, etc.)
    # TODO: Generate hash, resize images, extract metadata
    # TODO: AI-powered alt text generation

    return {"message": "Media upload endpoint - implementation pending"}


# Search and Discovery


@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
):
    """
    Get search suggestions for component discovery.
    Optimized to use a single query with UNION to prevent N+1 queries.
    """
    from sqlalchemy import text

    # Use a single optimized query with UNION to get both brands and part numbers
    query = text(
        """
        SELECT DISTINCT 'brand' as type, brand as value
        FROM components
        WHERE tenant_id = :tenant_id AND brand ILIKE :search_term

        UNION

        SELECT DISTINCT 'part_number' as type, part_number as value
        FROM components
        WHERE tenant_id = :tenant_id AND part_number ILIKE :search_term

        LIMIT 20
    """
    )

    results = db.execute(
        query, {"tenant_id": current_user["tenant_id"], "search_term": f"{q}%"}
    ).fetchall()

    brands = [r.value for r in results if r.type == "brand"][:10]
    part_numbers = [r.value for r in results if r.type == "part_number"][:10]

    return {"brands": brands, "part_numbers": part_numbers}


@router.get("/stats/summary")
@cached_response(ttl=600, include_user=False)  # Cache longer, not user-specific
@rate_limit(requests_per_minute=50)
@performance_metrics
async def get_component_stats(
    db: Session = Depends(SessionDep), current_user: dict = Depends(get_current_user)
):
    """
    Get component statistics for dashboard.
    """
    tenant_id = current_user["tenant_id"]

    # Total components
    total_components = (
        db.query(models.Component).filter(models.Component.tenant_id == tenant_id).count()
    )

    # Active components
    active_states = [
        models.ComponentStatusEnum.APPROVED,
        models.ComponentStatusEnum.AVAILABLE,
        models.ComponentStatusEnum.RFQ_OPEN,
        models.ComponentStatusEnum.RFQ_AWARDED,
        models.ComponentStatusEnum.PURCHASING,
        models.ComponentStatusEnum.ORDERED,
        models.ComponentStatusEnum.SHIPPED,
        models.ComponentStatusEnum.RECEIVED,
        models.ComponentStatusEnum.INSTALLED,
        models.ComponentStatusEnum.COMMISSIONED,
        models.ComponentStatusEnum.OPERATIONAL,
        models.ComponentStatusEnum.WARRANTY_ACTIVE,
    ]

    active_components = (
        db.query(models.Component)
        .filter(
            and_(
                models.Component.tenant_id == tenant_id,
                models.Component.status.in_([s.value for s in active_states]),
            )
        )
        .count()
    )

    # Optimized: Get category and domain stats in a single query using subqueries
    from sqlalchemy import case

    # Single query to get all category stats
    category_stats = (
        db.query(models.Component.category, func.count(models.Component.id).label("count"))
        .filter(models.Component.tenant_id == tenant_id)
        .group_by(models.Component.category)
        .all()
    )

    # Single query to get all domain stats
    domain_stats = (
        db.query(models.Component.domain, func.count(models.Component.id).label("count"))
        .filter(models.Component.tenant_id == tenant_id)
        .group_by(models.Component.domain)
        .all()
    )

    return {
        "total_components": total_components,
        "active_components": active_components,
        "draft_components": db.query(models.Component)
        .filter(
            and_(
                models.Component.tenant_id == tenant_id,
                models.Component.status == models.ComponentStatusEnum.DRAFT,
            )
        )
        .count(),
        "categories": {cat[0] or "uncategorized": cat[1] for cat in category_stats},
        "domains": {dom[0] or "unspecified": dom[1] for dom in domain_stats},
    }
