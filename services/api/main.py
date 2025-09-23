"""
OriginFD API Gateway - Main FastAPI Application
"""

import logging
import os
import time
from contextlib import asynccontextmanager

import uvicorn

# Include core API routers
from api.routers import (  # alarms,; approvals,; commerce,; documents,; orchestrator,; projects,  # Temporarily disabled
    auth,
    health,
)
from core.config import get_settings
from core.database import get_engine
from core.logging_config import setup_logging
from core.performance import compression_middleware, db_monitor, health_monitor
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from simple_components import router as simple_components_router

# Temporarily disabled: , auth
# from api.routers import commerce

# Temporarily disabled due to import issues:
# from api.routers import documents, marketplace, components, component_integration, suppliers

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("Starting OriginFD API Gateway...")
    settings = get_settings()

    # Warm up database connection
    if os.getenv("SKIP_DB_STARTUP", "0") != "1":
        try:
            with get_engine().connect() as conn:
                from sqlalchemy import text

                conn.execute(text("SELECT 1"))
            logger.info("Database connection verified")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    # TODO: Warm up caches, load tool registry, etc.
    logger.info("API Gateway startup complete")

    yield

    # Shutdown
    logger.info("Shutting down OriginFD API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="OriginFD API",
    description="Enterprise Solar PV, BESS & Hybrid Energy System Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()


# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """Monitor request performance and update health metrics."""
    start_time = time.time()
    health_monitor.request_count += 1

    try:
        response = await call_next(request)

        # Add performance headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log slow requests
        if process_time > 2.0:
            logging.warning(
                f"Slow request: {request.method} {request.url} took {process_time:.3f}s"
            )

        return response
    except Exception as e:
        health_monitor.error_count += 1
        raise


# Add middleware in correct order (last added = first executed)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporarily disabled TrustedHostMiddleware for development
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=settings.ALLOWED_HOSTS
# )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Include routers - temporarily reduced for testing
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
# app.include_router(projects.router, prefix="/projects", tags=["projects"])  # Temporarily disabled
# app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
# app.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
# app.include_router(documents.router, prefix="/documents", tags=["documents"])
# app.include_router(documents.project_router, prefix="/projects", tags=["documents"])
# app.include_router(simple_components_router, prefix="/components", tags=["components"])
# app.include_router(commerce.router, prefix="/commerce", tags=["commerce"])
# app.include_router(orchestrator.router, prefix="/orchestrator", tags=["orchestrator"])

# app.include_router(component_integration.router, prefix="/component-integration", tags=["component-integration"])
# app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
# app.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OriginFD API Gateway",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "performance": {
            "requests_processed": health_monitor.request_count,
            "error_rate": f"{(health_monitor.error_count / max(health_monitor.request_count, 1) * 100):.2f}%",
        },
    }


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with performance metrics."""
    return await health_monitor.get_health_status()


# In-memory storage for projects, documents, and components (replace with database later)
projects_store = {}
documents_store = {}
components_store = {}
views_store = {}


@app.get("/projects/")
async def list_projects():
    """List all projects."""
    projects_list = list(projects_store.values())
    return {
        "projects": projects_list,
        "total": len(projects_list),
        "page": 1,
        "page_size": 20,
    }


@app.post("/projects/")
async def create_project(project_data: dict):
    """Create a new project and store it."""
    import uuid
    from datetime import datetime

    # Generate a new project ID
    project_id = f"proj_{str(uuid.uuid4())[:8]}"

    # Create project response
    project_name = project_data.get("name", "Untitled Project")
    new_project = {
        "id": project_id,
        "project_name": project_name,
        "name": project_name,
        "domain": project_data.get("domain", "PV"),
        "scale": project_data.get("scale", "RESIDENTIAL"),
        "status": "DRAFT",
        "location": project_data.get("location", "Unknown"),
        "description": project_data.get("description", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "owner_id": "mock-user-id",
        "completion_percentage": 0,
        "display_status": "Draft",
        "tags": [],
        "document_id": f"{project_id}-main",
        "document_hash": None,
    }

    # Store the project
    projects_store[project_id] = new_project

    # Create a basic document for the project
    document = {
        "id": f"{project_id}-main",
        "project_name": project_name,
        "domain": new_project["domain"],
        "scale": new_project["scale"],
        "current_version": 1,
        "content_hash": "initial",
        "is_active": True,
        "created_at": new_project["created_at"],
        "updated_at": new_project["updated_at"],
        "document_data": {
            "project_info": {
                "name": project_name,
                "description": new_project["description"],
                "location": new_project["location"],
            },
            "components": [],
            "system_design": {},
        },
    }

    documents_store[f"{project_id}-main"] = document

    logger.info(f"Created project: {new_project}")
    return new_project


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project by ID."""
    if project_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_store[project_id]


@app.get("/projects/{project_id}/documents")
async def get_project_documents(project_id: str):
    """Get documents for a specific project."""
    if project_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")

    # Return documents associated with this project
    project_documents = []
    for doc_id, document in documents_store.items():
        if doc_id.startswith(project_id):
            project_documents.append(document)

    return project_documents


@app.get("/projects/{project_id}/lifecycle")
async def get_project_lifecycle(project_id: str):
    """Get project lifecycle phases and gates."""
    if project_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")

    # Return standard project lifecycle phases for energy projects
    lifecycle = {
        "phases": [
            {
                "id": "concept",
                "name": "Concept Development",
                "status": "completed",
                "gates": [
                    {
                        "id": "gate-1",
                        "name": "Feasibility Gate",
                        "status": "approved",
                        "approved_by": "admin@originfd.com",
                        "approved_at": "2025-09-20T10:00:00Z",
                        "notes": "Project shows good technical and commercial feasibility",
                    }
                ],
            },
            {
                "id": "design",
                "name": "Design Phase",
                "status": "in_progress",
                "gates": [
                    {
                        "id": "gate-2",
                        "name": "Design Review Gate",
                        "status": "in_review",
                        "notes": "Preliminary design review in progress",
                    }
                ],
            },
            {
                "id": "procurement",
                "name": "Procurement",
                "status": "pending",
                "gates": [
                    {
                        "id": "gate-3",
                        "name": "Procurement Gate",
                        "status": "pending",
                        "notes": "Awaiting design completion",
                    }
                ],
            },
            {
                "id": "construction",
                "name": "Construction",
                "status": "pending",
                "gates": [
                    {
                        "id": "gate-4",
                        "name": "Construction Gate",
                        "status": "pending",
                        "notes": "Awaiting procurement completion",
                    }
                ],
            },
            {
                "id": "commissioning",
                "name": "Commissioning",
                "status": "pending",
                "gates": [
                    {
                        "id": "gate-5",
                        "name": "Final Gate",
                        "status": "pending",
                        "notes": "Project completion and handover",
                    }
                ],
            },
        ],
        "bottlenecks": [],
    }

    return lifecycle


@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    return documents_store[document_id]


# Components API endpoints
@app.get("/components")
async def list_components(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    category: str = None,
    domain: str = None,
    status: str = None,
):
    """List available components for drag and drop."""

    # Initialize sample components if store is empty
    if not components_store:
        _initialize_sample_components()

    # Initialize demo projects if store is empty
    if not projects_store:
        _initialize_demo_projects()

    # Apply filters
    filtered_components = list(components_store.values())

    if search:
        filtered_components = [
            c for c in filtered_components if search.lower() in c["name"].lower()
        ]
    if category:
        filtered_components = [
            c for c in filtered_components if c["category"] == category
        ]
    if domain:
        filtered_components = [c for c in filtered_components if c["domain"] == domain]
    if status:
        filtered_components = [c for c in filtered_components if c["status"] == status]

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_components = filtered_components[start:end]

    return {
        "components": paginated_components,
        "total": len(filtered_components),
        "page": page,
        "page_size": page_size,
    }


@app.post("/components")
async def create_component(request: dict):
    """Create a new component following ODL-SD v4.1 standards."""
    if not components_store:
        _initialize_sample_components()

    # Generate unique component ID
    import uuid
    from datetime import datetime

    component_id = f"comp_{str(uuid.uuid4())[:8]}"

    # Extract basic info from request
    name = request.get("name", "Unknown Component")
    category = request.get("category", "general")
    domain = request.get("domain", "PV")
    scale = request.get("scale", "RESIDENTIAL")
    description = request.get("description", "")

    # Create ODL-SD v4.1 compliant component structure
    new_component = {
        "id": component_id,
        "component_management": {
            "component_identity": {
                "brand": request.get("brand", "Generic"),
                "part_number": request.get("part_number", f"PN-{component_id}"),
                "rating_w": request.get("rating_w", 1000),
                "classification": {"unspsc": request.get("unspsc", "26111704")},
            },
            "status": "available",
            "compliance": {
                "certificates": [{"standard": "IEC 61215", "valid_until": "2026-12-31"}]
            },
            "warranty": {
                "terms": {"duration_years": request.get("warranty_years", 10)}
            },
            "inventory": {
                "stocks": [{"on_hand_qty": request.get("stock_quantity", 50)}]
            },
        },
        "category": category,
        "domain": domain,
        "scale": scale,
        "description": description,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    # Store the component
    components_store[component_id] = new_component

    return {
        "id": component_id,
        "message": "Component created successfully",
        "component": new_component,
    }


@app.get("/components/stats")
async def get_component_stats():
    """Get component statistics."""
    if not components_store:
        _initialize_sample_components()

    total = len(components_store)
    categories = {}
    domains = {}

    for component in components_store.values():
        cat = component["category"]
        dom = component["domain"]
        categories[cat] = categories.get(cat, 0) + 1
        domains[dom] = domains.get(dom, 0) + 1

    return {
        "total": total,
        "categories": categories,
        "by_category": categories,
        "by_domain": domains,
    }


@app.get("/components/{component_id}")
async def get_component(component_id: str):
    """Get a specific component by ID."""
    if component_id not in components_store:
        raise HTTPException(status_code=404, detail="Component not found")
    return components_store[component_id]


# Views/Canvas API endpoints
@app.get("/projects/{project_id}/views")
async def get_project_views(project_id: str):
    """Get available views/canvases for a project."""
    if project_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")

    # Return default views for a project
    return [
        {
            "id": "sld-mv",
            "name": "Single Line Diagram - MV",
            "type": "sld",
            "canvas_type": "electrical",
            "description": "Medium voltage single line diagram",
        },
        {
            "id": "sld-lv",
            "name": "Single Line Diagram - LV",
            "type": "sld",
            "canvas_type": "electrical",
            "description": "Low voltage single line diagram",
        },
        {
            "id": "layout",
            "name": "Site Layout",
            "type": "layout",
            "canvas_type": "mechanical",
            "description": "Physical site layout view",
        },
    ]


@app.get("/views/{canvas_id}")
async def get_canvas_view(canvas_id: str, projectId: str = None):
    """Get canvas view data."""
    view_key = f"{projectId}_{canvas_id}" if projectId else canvas_id

    # Always create a demo SLD design for any canvas request
    # This ensures that the Components button has working drag/drop functionality
    demo_canvas = {
        "id": canvas_id,
        "project_id": projectId,
        "components": [
            {
                "id": "comp_1",
                "component_id": "solar-panel-1",
                "name": "Solar Panel Array (4kW)",
                "type": "solar_panel",
                "position": {"x": 100, "y": 200},
                "size": {"width": 80, "height": 60},
                "properties": {
                    "power_rating": 400,
                    "quantity": 10,
                    "total_power": 4000,
                    "voltage": 24.5,
                    "manufacturer": "SunPower",
                },
            },
            {
                "id": "comp_2",
                "component_id": "inverter-1",
                "name": "String Inverter (5kW)",
                "type": "inverter",
                "position": {"x": 320, "y": 200},
                "size": {"width": 60, "height": 40},
                "properties": {
                    "power_rating": 5000,
                    "efficiency": 0.978,
                    "input_voltage": 600,
                    "output_voltage": 480,
                },
            },
            {
                "id": "comp_3",
                "component_id": "meter-1",
                "name": "Energy Meter",
                "type": "meter",
                "position": {"x": 520, "y": 200},
                "size": {"width": 40, "height": 40},
                "properties": {
                    "voltage": 480,
                    "type": "bidirectional",
                    "accuracy": "Class 1",
                },
            },
            {
                "id": "comp_4",
                "component_id": "transformer-1",
                "name": "Grid Transformer",
                "type": "transformer",
                "position": {"x": 720, "y": 200},
                "size": {"width": 60, "height": 80},
                "properties": {
                    "power_rating": 100000,
                    "primary_voltage": 11000,
                    "secondary_voltage": 400,
                    "transformer_type": "step-down",
                },
            },
            {
                "id": "comp_5",
                "component_id": "battery-1",
                "name": "Battery Storage (10kWh)",
                "type": "battery",
                "position": {"x": 320, "y": 320},
                "size": {"width": 70, "height": 50},
                "properties": {
                    "capacity": 10000,
                    "voltage": 48,
                    "chemistry": "LiFePO4",
                    "cycles": 6000,
                },
            },
        ],
        "connections": [
            {
                "id": "conn_1",
                "from": "comp_1",
                "to": "comp_2",
                "from_port": "dc_output",
                "to_port": "dc_input",
                "type": "dc_cable",
                "properties": {
                    "voltage": 600,
                    "current": 20,
                    "cable_type": "DC",
                    "wire_gauge": "12 AWG",
                },
            },
            {
                "id": "conn_2",
                "from": "comp_2",
                "to": "comp_3",
                "from_port": "ac_output",
                "to_port": "line_input",
                "type": "ac_cable",
                "properties": {
                    "voltage": 480,
                    "current": 15,
                    "cable_type": "3-phase AC",
                    "frequency": 60,
                },
            },
            {
                "id": "conn_3",
                "from": "comp_3",
                "to": "comp_4",
                "from_port": "line_output",
                "to_port": "secondary",
                "type": "ac_cable",
                "properties": {
                    "voltage": 480,
                    "current": 15,
                    "cable_type": "3-phase AC",
                    "protection": "circuit_breaker",
                },
            },
            {
                "id": "conn_4",
                "from": "comp_2",
                "to": "comp_5",
                "from_port": "battery_port",
                "to_port": "dc_input",
                "type": "dc_cable",
                "properties": {
                    "voltage": 48,
                    "current": 200,
                    "cable_type": "DC",
                    "bidirectional": True,
                },
            },
        ],
        "canvas_data": {
            "zoom": 1.0,
            "pan": {"x": 0, "y": 0},
            "grid": {"enabled": True, "size": 20},
            "snap": {"enabled": True, "grid": True},
        },
        "metadata": {
            "title": "Sample Solar + Battery System",
            "description": "4kW solar with 10kWh battery storage and grid connection",
            "created_at": "2025-09-23T13:00:00Z",
            "version": "1.0",
        },
    }

    # Store the demo canvas
    views_store[view_key] = demo_canvas
    return demo_canvas


@app.patch("/views/{canvas_id}/overrides")
async def patch_view_overrides(canvas_id: str, positions: dict):
    """Update component positions on canvas."""
    # This endpoint is used to save component positions after drag/drop
    view_key = canvas_id
    if canvas_id not in views_store:
        views_store[view_key] = {"id": canvas_id, "components": [], "positions": {}}

    if "positions" not in views_store[view_key]:
        views_store[view_key]["positions"] = {}

    views_store[view_key]["positions"].update(positions)
    return {"ok": True}


@app.get("/views/{canvas_id}/overrides")
async def get_view_overrides(canvas_id: str):
    """Get component position overrides for canvas."""
    view_key = canvas_id
    if view_key not in views_store:
        return {}

    return views_store[view_key].get("positions", {})


def _initialize_sample_components():
    """Initialize ODL-SD v4.1 compliant components."""
    sample_components = [
        {
            "id": "solar-panel-1",
            "component_management": {
                "component_identity": {
                    "brand": "SunPower",
                    "part_number": "SPR-400-COM",
                    "rating_w": 400,
                    "classification": {"unspsc": "26111704"},  # PV Modules
                },
                "status": "available",
                "compliance": {
                    "certificates": [
                        {"standard": "IEC 61215", "valid_until": "2026-12-31"},
                        {"standard": "UL 1703", "valid_until": "2027-06-30"},
                    ]
                },
                "warranty": {"terms": {"duration_years": 25}},
                "inventory": {"stocks": [{"on_hand_qty": 150}]},
            },
            "category": "generation",
            "domain": "PV",
            "created_at": "2025-09-23T09:00:00Z",
        },
        {
            "id": "inverter-1",
            "component_management": {
                "component_identity": {
                    "brand": "SMA",
                    "part_number": "SB5.0-1SP-US-40",
                    "rating_w": 5000,
                    "classification": {"unspsc": "26111705"},  # Inverters
                },
                "status": "available",
                "compliance": {
                    "certificates": [
                        {"standard": "UL 1741", "valid_until": "2026-08-15"}
                    ]
                },
                "warranty": {"terms": {"duration_years": 10}},
                "inventory": {"stocks": [{"on_hand_qty": 25}]},
            },
            "category": "conversion",
            "domain": "PV",
            "created_at": "2025-09-23T09:00:00Z",
        },
        {
            "id": "battery-1",
            "component_management": {
                "component_identity": {
                    "brand": "Tesla",
                    "part_number": "Powerwall-2",
                    "rating_w": 5000,
                    "classification": {"unspsc": "26111706"},  # Batteries
                },
                "status": "available",
                "compliance": {
                    "certificates": [
                        {"standard": "UL 9540", "valid_until": "2026-11-20"}
                    ]
                },
                "warranty": {"terms": {"duration_years": 10}},
                "inventory": {"stocks": [{"on_hand_qty": 8}]},
            },
            "category": "storage",
            "domain": "BESS",
            "created_at": "2025-09-23T09:00:00Z",
        },
        {
            "id": "transformer-1",
            "component_management": {
                "component_identity": {
                    "brand": "ABB",
                    "part_number": "DT-100-11/0.4",
                    "rating_w": 100000,
                    "classification": {"unspsc": "26111707"},  # Transformers
                },
                "status": "available",
                "compliance": {
                    "certificates": [
                        {"standard": "IEEE C57.12.20", "valid_until": "2028-01-10"}
                    ]
                },
                "warranty": {"terms": {"duration_years": 20}},
                "inventory": {"stocks": [{"on_hand_qty": 3}]},
            },
            "category": "distribution",
            "domain": "GRID",
            "created_at": "2025-09-23T09:00:00Z",
        },
        {
            "id": "switch-1",
            "component_management": {
                "component_identity": {
                    "brand": "Schneider Electric",
                    "part_number": "SW60-DC-3P-600",
                    "rating_w": 0,
                    "classification": {"unspsc": "26111708"},  # Protection
                },
                "status": "available",
                "compliance": {
                    "certificates": [
                        {"standard": "UL 98B", "valid_until": "2026-09-25"}
                    ]
                },
                "warranty": {"terms": {"duration_years": 5}},
                "inventory": {"stocks": [{"on_hand_qty": 45}]},
            },
            "category": "protection",
            "domain": "PV",
            "created_at": "2025-09-23T09:00:00Z",
        },
        {
            "id": "meter-1",
            "component_management": {
                "component_identity": {
                    "brand": "Landis+Gyr",
                    "part_number": "E650",
                    "rating_w": 0,
                    "classification": {"unspsc": "26111709"},  # Monitoring
                },
                "status": "available",
                "compliance": {
                    "certificates": [
                        {"standard": "ANSI C12.20", "valid_until": "2027-12-31"}
                    ]
                },
                "warranty": {"terms": {"duration_years": 15}},
                "inventory": {"stocks": [{"on_hand_qty": 20}]},
            },
            "category": "monitoring",
            "domain": "GRID",
            "created_at": "2025-09-23T09:00:00Z",
        },
    ]

    for component in sample_components:
        components_store[component["id"]] = component


def _initialize_demo_projects():
    """Initialize demo projects for persistence testing."""
    demo_projects = [
        {
            "id": "proj_demo_001",
            "project_name": "Demo Solar Project",
            "name": "Demo Solar Project",
            "domain": "PV",
            "scale": "RESIDENTIAL",
            "status": "DRAFT",
            "location": "California, USA",
            "description": "Demo project with 4kW solar + 10kWh battery",
            "created_at": "2025-09-23T12:00:00Z",
            "updated_at": "2025-09-23T12:00:00Z",
            "owner_id": "mock-user-id",
            "completion_percentage": 25,
            "display_status": "Draft",
            "tags": ["demo", "residential", "solar"],
            "document_id": "proj_demo_001-main",
            "document_hash": None,
        },
        {
            "id": "proj_demo_002",
            "project_name": "Demo Commercial Project",
            "name": "Demo Commercial Project",
            "domain": "HYBRID",
            "scale": "COMMERCIAL",
            "status": "DRAFT",
            "location": "Texas, USA",
            "description": "Demo commercial hybrid system",
            "created_at": "2025-09-23T11:00:00Z",
            "updated_at": "2025-09-23T11:30:00Z",
            "owner_id": "mock-user-id",
            "completion_percentage": 45,
            "display_status": "Draft",
            "tags": ["demo", "commercial", "hybrid"],
            "document_id": "proj_demo_002-main",
            "document_hash": None,
        },
    ]

    for project in demo_projects:
        projects_store[project["id"]] = project
        # Create matching documents
        documents_store[project["document_id"]] = {
            "id": project["document_id"],
            "project_name": project["name"],
            "domain": project["domain"],
            "scale": project["scale"],
            "current_version": 1,
            "content_hash": "demo-hash-" + project["id"],
            "is_active": True,
            "created_at": project["created_at"],
            "updated_at": project["updated_at"],
            "project_metadata": {
                "name": project["name"],
                "description": project["description"],
                "location": project["location"],
            },
            "components": [],
            "system_design": {},
        }


if __name__ == "__main__":
    import os

    settings = get_settings()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
