"""
OriginFD API Gateway - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from core.config import get_settings
from core.database import engine
from core.logging_config import setup_logging
# Include core API routers
from api.routers import health, projects, alarms
# Temporarily disabled due to import issues:
# from api.routers import auth, documents, marketplace, components, component_integration, suppliers

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
    try:
        with engine.connect() as conn:
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
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Add middleware
# Temporarily disabled CORS middleware for testing
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_HOSTS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(alarms.router, prefix="/alarms", tags=["alarms"])

# Temporarily disabled due to import issues:
# app.include_router(auth.router, prefix="/auth", tags=["authentication"])
# app.include_router(documents.router, prefix="/odl", tags=["documents"])
# app.include_router(components.router, prefix="/components", tags=["components"])
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
        "docs": "/docs"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )