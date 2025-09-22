"""
OriginFD API Gateway - Main FastAPI Application
"""

import logging
import os
import time
from contextlib import asynccontextmanager

import uvicorn

# Include core API routers
from api.routers import (
    alarms,
    approvals,
    auth,
    commerce,
    documents,
    health,
    orchestrator,
    projects,
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


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(documents.project_router, prefix="/projects", tags=["documents"])
app.include_router(simple_components_router, prefix="/components", tags=["components"])
app.include_router(commerce.router, prefix="/commerce", tags=["commerce"])
app.include_router(orchestrator.router, prefix="/orchestrator", tags=["orchestrator"])

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
