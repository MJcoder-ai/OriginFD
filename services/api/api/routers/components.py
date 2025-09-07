"""
Component management API endpoints.
Implements ODL-SD v4.1 Component Management lifecycle.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
import uuid
import logging

from core.database import SessionDep
from core.security import get_current_user
from models.component import (
    Component, ComponentManagement, ComponentStatusEnum,
    Supplier, SupplierStatusEnum,
    MediaAsset, MediaAssetTypeEnum, MediaScopeEnum,
    InventoryRecord
)

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
    new_status: ComponentStatusEnum
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
async def create_component(
    request: ComponentCreateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new component in draft status.
    """
    try:
        # Generate component ID and name
        component_id = f"CMP:{request.brand}:{request.part_number}:{request.rating_w}W:REV1"
        name = f"{request.brand}_{request.part_number}_{request.rating_w}W"
        
        # Check for duplicates
        existing = db.query(Component).filter(
            or_(
                Component.component_id == component_id,
                Component.name == name
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Component with this ID or name already exists"
            )
        
        # Create component
        component = Component(
            tenant_id=uuid.UUID(current_user["tenant_id"]),
            component_id=component_id,
            brand=request.brand,
            part_number=request.part_number,
            rating_w=request.rating_w,
            name=name,
            status=ComponentStatusEnum.DRAFT,
            category=request.category,
            subcategory=request.subcategory,
            domain=request.domain,
            scale=request.scale,
            classification=request.classification,
            created_by=uuid.UUID(current_user["id"])
        )
        
        db.add(component)
        db.flush()  # Get the component ID
        
        # Create component management record
        management = ComponentManagement(
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
            media={"library": [], "capture_policy": {}, "doc_bindings": {"bindings": []}}
        )
        
        db.add(management)
        db.commit()
        db.refresh(component)
        
        logger.info(f"Created component {component.component_id} by user {current_user['id']}")
        
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
            created_by=str(component.created_by) if component.created_by else None
        )
        
    except Exception as e:
        logger.error(f"Failed to create component: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create component: {str(e)}"
        )


@router.get("/", response_model=ComponentListResponse)
async def list_components(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ComponentStatusEnum] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = Query(False)
):
    """
    List components with filtering and pagination.
    """
    query = db.query(Component).filter(Component.tenant_id == current_user["tenant_id"])
    
    # Apply filters
    if status:
        query = query.filter(Component.status == status)
    
    if category:
        query = query.filter(Component.category == category)
    
    if domain:
        query = query.filter(Component.domain == domain)
        
    if brand:
        query = query.filter(Component.brand.ilike(f"%{brand}%"))
    
    if active_only:
        active_states = [
            ComponentStatusEnum.APPROVED,
            ComponentStatusEnum.AVAILABLE,
            ComponentStatusEnum.RFQ_OPEN,
            ComponentStatusEnum.RFQ_AWARDED,
            ComponentStatusEnum.PURCHASING,
            ComponentStatusEnum.ORDERED,
            ComponentStatusEnum.SHIPPED,
            ComponentStatusEnum.RECEIVED,
            ComponentStatusEnum.INSTALLED,
            ComponentStatusEnum.COMMISSIONED,
            ComponentStatusEnum.OPERATIONAL,
            ComponentStatusEnum.WARRANTY_ACTIVE
        ]
        query = query.filter(Component.status.in_([s.value for s in active_states]))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Component.name.ilike(search_term),
                Component.brand.ilike(search_term),
                Component.part_number.ilike(search_term),
                Component.component_id.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    components = query.order_by(Component.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert to response models
    component_responses = []
    for comp in components:
        component_responses.append(ComponentResponse(
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
            created_by=str(comp.created_by) if comp.created_by else None
        ))
    
    return ComponentListResponse(
        components=component_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{component_id}", response_model=ComponentResponse)
async def get_component(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific component by ID.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format"
        )
    
    component = db.query(Component).filter(
        and_(
            Component.id == component_uuid,
            Component.tenant_id == current_user["tenant_id"]
        )
    ).first()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
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
        created_by=str(component.created_by) if component.created_by else None
    )


@router.patch("/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: str,
    request: ComponentUpdateRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a component.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format"
        )
    
    component = db.query(Component).filter(
        and_(
            Component.id == component_uuid,
            Component.tenant_id == current_user["tenant_id"]
        )
    ).first()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field in ['brand', 'part_number', 'rating_w'] and value is not None:
            # If core identity fields change, regenerate component_id and name
            setattr(component, field, value)
            
    # Regenerate component_id and name if identity fields changed
    if any(field in update_data for field in ['brand', 'part_number', 'rating_w']):
        component.component_id = f"CMP:{component.brand}:{component.part_number}:{component.rating_w}W:REV1"
        component.name = f"{component.brand}_{component.part_number}_{component.rating_w}W"
    
    # Update other fields
    for field, value in update_data.items():
        if field not in ['brand', 'part_number', 'rating_w']:
            setattr(component, field, value)
    
    component.updated_by = uuid.UUID(current_user["id"])
    component.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(component)
    
    logger.info(f"Updated component {component.component_id} by user {current_user['id']}")
    
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
        created_by=str(component.created_by) if component.created_by else None
    )


@router.delete("/{component_id}")
async def delete_component(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Archive a component (soft delete).
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format"
        )
    
    component = db.query(Component).filter(
        and_(
            Component.id == component_uuid,
            Component.tenant_id == current_user["tenant_id"]
        )
    ).first()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    # Archive instead of hard delete
    component.status = ComponentStatusEnum.ARCHIVED
    component.updated_by = uuid.UUID(current_user["id"])
    component.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Archived component {component.component_id} by user {current_user['id']}")
    
    return {"message": "Component archived successfully"}


# Component Status Transitions

@router.post("/{component_id}/transition", response_model=ComponentResponse)
async def transition_component_status(
    component_id: str,
    request: ComponentStatusTransitionRequest,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Transition component status with validation.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format"
        )
    
    component = db.query(Component).filter(
        and_(
            Component.id == component_uuid,
            Component.tenant_id == current_user["tenant_id"]
        )
    ).first()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    # Validate transition
    if not component.can_transition_to(request.new_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {component.status} to {request.new_status.value}"
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
            diff=f"Status changed from {old_status} to {request.new_status.value}"
        )
    
    db.commit()
    db.refresh(component)
    
    logger.info(f"Transitioned component {component.component_id} from {old_status} to {request.new_status.value}")
    
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
        created_by=str(component.created_by) if component.created_by else None
    )


# Media Management

@router.get("/{component_id}/media", response_model=List[MediaAssetResponse])
async def list_component_media(
    component_id: str,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user),
    asset_type: Optional[MediaAssetTypeEnum] = None
):
    """
    List media assets for a component.
    """
    try:
        component_uuid = uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component ID format"
        )
    
    # Verify component exists and user has access
    component = db.query(Component).filter(
        and_(
            Component.id == component_uuid,
            Component.tenant_id == current_user["tenant_id"]
        )
    ).first()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    query = db.query(MediaAsset).filter(MediaAsset.component_id == component_uuid)
    
    if asset_type:
        query = query.filter(MediaAsset.type == asset_type.value)
    
    media_assets = query.order_by(MediaAsset.created_at.desc()).all()
    
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
            created_at=asset.created_at
        )
        for asset in media_assets
    ]


@router.post("/{component_id}/media/upload")
async def upload_component_media(
    component_id: str,
    file: UploadFile = File(...),
    asset_type: MediaAssetTypeEnum = MediaAssetTypeEnum.COMPONENT_PHOTO_HERO,
    scope: MediaScopeEnum = MediaScopeEnum.COMPONENT_GENERIC,
    alt_text: Optional[str] = None,
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
):
    """
    Get search suggestions for component discovery.
    """
    suggestions = db.query(Component.brand).filter(
        and_(
            Component.tenant_id == current_user["tenant_id"],
            Component.brand.ilike(f"{q}%")
        )
    ).distinct().limit(10).all()
    
    brand_suggestions = [s[0] for s in suggestions]
    
    part_suggestions = db.query(Component.part_number).filter(
        and_(
            Component.tenant_id == current_user["tenant_id"],
            Component.part_number.ilike(f"{q}%")
        )
    ).distinct().limit(10).all()
    
    part_suggestions = [s[0] for s in part_suggestions]
    
    return {
        "brands": brand_suggestions,
        "part_numbers": part_suggestions
    }


@router.get("/stats/summary")
async def get_component_stats(
    db: Session = Depends(SessionDep),
    current_user: dict = Depends(get_current_user)
):
    """
    Get component statistics for dashboard.
    """
    tenant_id = current_user["tenant_id"]
    
    # Total components
    total_components = db.query(Component).filter(Component.tenant_id == tenant_id).count()
    
    # Active components
    active_states = [
        ComponentStatusEnum.APPROVED,
        ComponentStatusEnum.AVAILABLE,
        ComponentStatusEnum.RFQ_OPEN,
        ComponentStatusEnum.RFQ_AWARDED,
        ComponentStatusEnum.PURCHASING,
        ComponentStatusEnum.ORDERED,
        ComponentStatusEnum.SHIPPED,
        ComponentStatusEnum.RECEIVED,
        ComponentStatusEnum.INSTALLED,
        ComponentStatusEnum.COMMISSIONED,
        ComponentStatusEnum.OPERATIONAL,
        ComponentStatusEnum.WARRANTY_ACTIVE
    ]
    
    active_components = db.query(Component).filter(
        and_(
            Component.tenant_id == tenant_id,
            Component.status.in_([s.value for s in active_states])
        )
    ).count()
    
    # Components by category
    category_stats = db.query(
        Component.category,
        func.count(Component.id).label('count')
    ).filter(
        Component.tenant_id == tenant_id
    ).group_by(Component.category).all()
    
    # Components by domain
    domain_stats = db.query(
        Component.domain,
        func.count(Component.id).label('count')
    ).filter(
        Component.tenant_id == tenant_id
    ).group_by(Component.domain).all()
    
    return {
        "total_components": total_components,
        "active_components": active_components,
        "draft_components": db.query(Component).filter(
            and_(Component.tenant_id == tenant_id, Component.status == ComponentStatusEnum.DRAFT)
        ).count(),
        "categories": {cat[0] or "uncategorized": cat[1] for cat in category_stats},
        "domains": {dom[0] or "unspecified": dom[1] for dom in domain_stats}
    }
