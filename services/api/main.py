"""
OriginFD API Gateway - Main FastAPI Application
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from importlib import import_module

import uvicorn
from core.config import get_settings
from core.database import get_engine
from core.logging_config import setup_logging
from core.performance import health_monitor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Include core API routers
from services.api.api.routers import auth, health, projects

# Temporarily disabled: , auth
# from api.routers import commerce

# Temporarily disabled due to import issues:
# from api.routers import documents, marketplace, components,
# component_integration, suppliers

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


# Non-blocking prestart (migrate + seed); opt-in via API_ENABLE_PRESTART
if os.getenv("API_ENABLE_PRESTART", "0") in {"1", "true", "True"}:
    try:
        from services.api import prestart as _prestart  # noqa: F401

        _prestart.main()
    except Exception:  # pragma: no cover
        import logging as _logging

        _logging.getLogger(__name__).warning(
            "prestart skipped (dev env or missing settings)"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("Starting OriginFD API Gateway...")
    get_settings()  # Initialize settings

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
    except Exception:
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


# Include routers - production architecture enabled
app.include_router(health.router, prefix="/health", tags=["health"])
_DEFAULT_OPTIONAL_ROUTER_MODULES = {
    "services.api.api.routers.documents",
    "services.api.api.routers.documents.project_router",
    "services.api.api.routers.components",
    "services.api.api.routers.commerce",
    "services.api.api.routers.orchestrator",
    "services.api.api.routers.component_integration",
    "services.api.api.routers.suppliers",
    "services.api.api.routers.marketplace",
}
_ENV_OPTIONAL_ROUTER_MODULES = {
    entry.strip()
    for entry in os.getenv("API_OPTIONAL_ROUTERS", "").split(",")
    if entry.strip()
}
_OPTIONAL_ROUTER_MODULES = (
    _DEFAULT_OPTIONAL_ROUTER_MODULES | _ENV_OPTIONAL_ROUTER_MODULES
)


app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])

_OPTIONAL_ROUTERS = [
    ("services.api.api.routers.approvals", "/approvals", ["approvals"]),
    ("services.api.api.routers.alarms", "/alarms", ["alarms"]),
    ("services.api.api.routers.documents", "/documents", ["documents"]),
    (
        "services.api.api.routers.documents",
        "/projects",
        ["documents"],
        "project_router",
    ),
    ("services.api.api.routers.components", "/components", ["components"]),
    ("services.api.api.routers.commerce", "/commerce", ["commerce"]),
    ("services.api.api.routers.orchestrator", "/orchestrator", ["orchestrator"]),
    (
        "services.api.api.routers.component_integration",
        "/component-integration",
        ["component-integration"],
    ),
    ("services.api.api.routers.suppliers", "/suppliers", ["suppliers"]),
    ("services.api.api.routers.marketplace", "/marketplace", ["marketplace"]),
]
for module_path, prefix, tags, *attr in _OPTIONAL_ROUTERS:
    router_attr = attr[0] if attr else "router"
    module_key = f"{module_path}.{router_attr}" if attr else module_path
    try:
        module = import_module(module_path)
        router_obj = getattr(module, router_attr)
    except Exception as exc:  # pragma: no cover - optional wiring
        if (
            module_key in _OPTIONAL_ROUTER_MODULES
            or module_path in _OPTIONAL_ROUTER_MODULES
        ):
            logger.warning(
                "Skipping optional router %s.%s: %s",
                module_path,
                router_attr if attr else "router",
                exc,
            )
            continue
        raise
    app.include_router(router_obj, prefix=prefix, tags=tags)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    error_rate = health_monitor.error_count / max(health_monitor.request_count, 1) * 100
    return {
        "name": "OriginFD API Gateway",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "performance": {
            "requests_processed": health_monitor.request_count,
            "error_rate": f"{error_rate:.2f}%",
        },
    }


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with performance metrics."""
    return await health_monitor.get_health_status()


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
