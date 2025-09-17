"""
Health check endpoints for monitoring and load balancer health checks.
"""

import os
import time
from typing import Any, Dict

import psutil
from core.config import get_settings
from core.database import check_database_connection
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: float
    version: str
    environment: str
    uptime_seconds: float


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""

    status: str
    timestamp: float
    version: str
    environment: str
    uptime_seconds: float
    services: Dict[str, Any]
    system: Dict[str, Any]


# Track application start time for uptime calculation
start_time = time.time()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is healthy.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=time.time() - start_time,
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 if the service is ready to serve traffic.
    """
    settings = get_settings()

    # Check database connection
    db_healthy = await check_database_connection()
    if not db_healthy:
        raise HTTPException(status_code=503, detail="Database connection failed")

    # TODO: Add Redis connection check
    # TODO: Add other service dependency checks

    return HealthResponse(
        status="ready",
        timestamp=time.time(),
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=time.time() - start_time,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check with system metrics.
    Use for monitoring and debugging.
    """
    settings = get_settings()

    # Check service dependencies
    db_healthy = await check_database_connection()

    services = {
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "url": (
                settings.DATABASE_URL.split("@")[-1]
                if "@" in settings.DATABASE_URL
                else "configured"
            ),
        },
        "redis": {
            "status": "unknown",  # TODO: Add Redis health check
            "url": (
                settings.REDIS_URL.split("@")[-1]
                if "@" in settings.REDIS_URL
                else "configured"
            ),
        },
    }

    # Get system metrics
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        system = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }
    except Exception as e:
        system = {"error": f"Could not get system metrics: {str(e)}"}

    # Determine overall status
    overall_status = "healthy"
    if not db_healthy:
        overall_status = "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=time.time(),
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=time.time() - start_time,
        services=services,
        system=system,
    )
