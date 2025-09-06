"""
OriginFD AI Orchestrator Service
L1 AI system with Planner/Router, Tool Registry, and Graph-RAG.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import uvicorn

from core.config import get_settings
from core.logging_config import setup_logging
from api.routers import tasks, tools, planning, health
from planner.orchestrator import AIOrchestrator

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("Starting OriginFD AI Orchestrator...")
    settings = get_settings()
    
    # Initialize AI orchestrator
    orchestrator = AIOrchestrator()
    await orchestrator.initialize()
    
    # Store orchestrator in app state
    app.state.orchestrator = orchestrator
    
    logger.info("AI Orchestrator startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OriginFD AI Orchestrator...")
    if hasattr(app.state, 'orchestrator'):
        await app.state.orchestrator.cleanup()


# Create FastAPI app
app = FastAPI(
    title="OriginFD AI Orchestrator",
    description="L1 AI system for ODL-SD document processing",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Get settings
settings = get_settings()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    logger.error(f"Unexpected error in orchestrator: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(planning.router, prefix="/planning", tags=["planning"])


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "name": "OriginFD AI Orchestrator",
        "version": "0.1.0",
        "status": "operational",
        "capabilities": [
            "task_planning",
            "tool_execution", 
            "graph_rag_grounding",
            "policy_routing",
            "batch_processing"
        ],
        "docs": "/docs"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )