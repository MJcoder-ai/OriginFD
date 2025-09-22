"""Smoke tests confirming primary routers are mounted on the main application."""

import os
import sys
from typing import Generator

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

PACKAGES_ROOT = os.path.join(PROJECT_ROOT, "packages", "py")
if PACKAGES_ROOT not in sys.path:
    sys.path.insert(0, PACKAGES_ROOT)

pytest_plugins = ["tests.integration.test_api_endpoints"]


@pytest.fixture(autouse=True)
def skip_metadata_creation(monkeypatch) -> Generator[None, None, None]:
    """Avoid creating database tables that require PostgreSQL-specific types."""
    from core.database import Base

    monkeypatch.setattr(Base.metadata, "create_all", lambda *args, **kwargs: None)
    monkeypatch.setattr(Base.metadata, "drop_all", lambda *args, **kwargs: None)
    yield


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/projects",
        "/approvals",
        "/alarms",
        "/documents",
        "/components",
        "/commerce",
    ],
)
def test_router_base_path_is_mounted(client, path):
    """Requests to each router prefix should resolve to a mounted route."""
    response = client.get(path)
    assert (
        response.status_code != 404
    ), f"Expected non-404 response for {path}, got {response.status_code}"
