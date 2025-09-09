import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.orchestrator.planner.region_router import RegionRouter, Region


@pytest.mark.asyncio
async def test_tenant_preference_region_selected():
    router = RegionRouter()
    region = await router._determine_target_region("tenant_eu", {})
    assert region == Region.EU_CENTRAL


@pytest.mark.asyncio
async def test_residency_rules_override_preferences():
    router = RegionRouter()
    context = {"data_residency_required": True, "user_location": "EU-DE"}
    region = await router._determine_target_region("tenant_us", context)
    assert region == Region.EU_CENTRAL


@pytest.mark.asyncio
async def test_default_region_without_preference():
    router = RegionRouter()
    region = await router._determine_target_region("unknown_tenant", {})
    assert region == Region.US_EAST
