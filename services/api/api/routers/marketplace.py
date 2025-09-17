"""
Marketplace endpoints - placeholder for future implementation.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def marketplace_root():
    """Marketplace root endpoint - coming soon."""
    return {
        "message": "Marketplace API coming soon",
        "version": "0.1.0",
        "features": ["component_catalog", "supplier_network", "rfq_system"],
    }
