"""Commerce API endpoints."""

import os
import sys

from fastapi import APIRouter

from services.commerce_core import escrow_manager, payout_ledger, psu_meter

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

router = APIRouter()


@router.get("/")
async def commerce_root() -> dict[str, list[str]]:
    """Provide discovery information for commerce routes."""
    return {
        "available_endpoints": [
            "GET /commerce/psu/{tenant_id}",
            "GET /commerce/escrow/{tenant_id}",
            "GET /commerce/transactions/{tenant_id}",
        ]
    }


@router.get("/psu/{tenant_id}")
async def get_psu_usage(tenant_id: str):
    """Retrieve PSU usage for a tenant."""
    return psu_meter.get_usage(tenant_id)


@router.get("/escrow/{tenant_id}")
async def get_escrow_status(tenant_id: str):
    """Retrieve escrow milestone status for a tenant."""
    return escrow_manager.get_status(tenant_id)


@router.get("/transactions/{tenant_id}")
async def get_transaction_history(tenant_id: str):
    """Retrieve payout transactions for a tenant."""
    return payout_ledger.get_history(tenant_id)
