"""
Simple component API router for ODL-SD integration.
Provides basic component management functionality.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

router = APIRouter()


# Simple data models for component management
class ComponentResponse(BaseModel):
    id: str
    component_id: str
    brand: str
    part_number: str
    rating_w: float
    name: str
    status: str = "available"
    category: Optional[str] = None
    subcategory: Optional[str] = None
    domain: Optional[str] = None
    scale: Optional[str] = None
    classification: Optional[dict] = None
    is_active: bool = True
    created_at: str
    updated_at: str
    created_by: Optional[str] = None


class ComponentCreateRequest(BaseModel):
    brand: str
    part_number: str
    rating_w: float
    category: Optional[str] = None
    subcategory: Optional[str] = None
    domain: Optional[str] = None
    scale: Optional[str] = None
    classification: Optional[dict] = None


class ComponentListResponse(BaseModel):
    components: List[ComponentResponse]
    total: int
    page: int
    page_size: int


class DatasheetParseResponse(BaseModel):
    """Response model for parsed datasheet attributes."""

    attributes: Dict[str, Any]


# Mock data for testing
MOCK_COMPONENTS = [
    ComponentResponse(
        id="1",
        component_id="PV_PANEL_001",
        brand="SunPower",
        part_number="SPR-MAX3-400",
        rating_w=400.0,
        name="SunPower SPR-MAX3-400 Solar Panel",
        category="generation",
        domain="PV",
        scale="RESIDENTIAL",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    ),
    ComponentResponse(
        id="2",
        component_id="BESS_001",
        brand="Tesla",
        part_number="Powerwall-2",
        rating_w=5000.0,
        name="Tesla Powerwall 2",
        category="storage",
        domain="BESS",
        scale="RESIDENTIAL",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    ),
    ComponentResponse(
        id="3",
        component_id="INV_001",
        brand="Enphase",
        part_number="IQ7PLUS-72-M-US",
        rating_w=290.0,
        name="Enphase IQ7PLUS Microinverter",
        category="conversion",
        domain="PV",
        scale="RESIDENTIAL",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    ),
]


@router.get("/", response_model=ComponentListResponse)
async def list_components(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """List components with filtering and pagination"""

    # Filter mock data
    filtered_components = MOCK_COMPONENTS.copy()

    if status:
        filtered_components = [c for c in filtered_components if c.status == status]

    if category:
        filtered_components = [c for c in filtered_components if c.category == category]

    if domain:
        filtered_components = [c for c in filtered_components if c.domain == domain]

    if brand:
        filtered_components = [
            c for c in filtered_components if brand.lower() in c.brand.lower()
        ]

    if search:
        search_lower = search.lower()
        filtered_components = [
            c
            for c in filtered_components
            if search_lower in c.brand.lower() or search_lower in c.part_number.lower()
        ]

    if active_only:
        filtered_components = [c for c in filtered_components if c.is_active]

    # Pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_components = filtered_components[start_idx:end_idx]

    return ComponentListResponse(
        components=paginated_components,
        total=len(filtered_components),
        page=page,
        page_size=page_size,
    )


@router.get("/{component_id}", response_model=ComponentResponse)
async def get_component(component_id: str):
    """Get specific component by ID"""
    component = next((c for c in MOCK_COMPONENTS if c.id == component_id), None)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.post("/", response_model=ComponentResponse)
async def create_component(request: ComponentCreateRequest):
    """Create new component"""
    new_component = ComponentResponse(
        id=str(len(MOCK_COMPONENTS) + 1),
        component_id=f"{request.domain or 'COMP'}_{request.part_number}",
        brand=request.brand,
        part_number=request.part_number,
        rating_w=request.rating_w,
        name=f"{request.brand} {request.part_number}",
        category=request.category,
        subcategory=request.subcategory,
        domain=request.domain,
        scale=request.scale,
        classification=request.classification,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        created_by="system",
    )

    MOCK_COMPONENTS.append(new_component)
    return new_component


@router.get("/stats/summary")
async def get_component_stats():
    """Get component statistics"""
    return {
        "total_components": len(MOCK_COMPONENTS),
        "active_components": len([c for c in MOCK_COMPONENTS if c.is_active]),
        "draft_components": 0,
        "categories": {
            "generation": len(
                [c for c in MOCK_COMPONENTS if c.category == "generation"]
            ),
            "storage": len([c for c in MOCK_COMPONENTS if c.category == "storage"]),
            "conversion": len(
                [c for c in MOCK_COMPONENTS if c.category == "conversion"]
            ),
        },
        "domains": {
            "PV": len([c for c in MOCK_COMPONENTS if c.domain == "PV"]),
            "BESS": len([c for c in MOCK_COMPONENTS if c.domain == "BESS"]),
            "HYBRID": len([c for c in MOCK_COMPONENTS if c.domain == "HYBRID"]),
        },
    }


@router.get("/search/suggestions")
async def get_search_suggestions(q: str = Query(...)):
    """Get search suggestions for brands and part numbers"""
    brands = set()
    part_numbers = set()

    q_lower = q.lower()

    for component in MOCK_COMPONENTS:
        if q_lower in component.brand.lower():
            brands.add(component.brand)
        if q_lower in component.part_number.lower():
            part_numbers.add(component.part_number)

    return {"brands": list(brands)[:10], "part_numbers": list(part_numbers)[:10]}


@router.post("/parse-datasheet", response_model=DatasheetParseResponse)
async def parse_datasheet(file: UploadFile = File(...)):
    """Parse an uploaded datasheet PDF and extract key attributes."""
    content = await file.read()
    text = ""
    try:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    except Exception:
        try:
            text = content.decode("utf-8")
        except Exception:
            text = ""

    attributes: Dict[str, Any] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key_norm = key.strip().lower().replace(" ", "_")
            attributes[key_norm] = value.strip()
        if len(attributes) >= 20:
            break

    if not attributes:
        attributes["raw_text"] = text[:1000]

    return DatasheetParseResponse(attributes=attributes)
