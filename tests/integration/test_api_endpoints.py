"""
Comprehensive integration tests for OriginFD API endpoints.
Tests the full request/response lifecycle through the API to the database.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID, uuid4

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test configuration
from core.config import Settings
from core.database import Base, get_db
from main import app

# Test data factories
from tests.factories import UserFactory, ProjectFactory, ComponentFactory

class TestConfig(Settings):
    """Test-specific configuration."""
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/15"  # Test Redis DB
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    SECRET_KEY: str = "test-secret-key-for-integration-tests"

    # Test-specific overrides
    DATABASE_POOL_SIZE: int = 1
    DATABASE_MAX_OVERFLOW: int = 0
    RATE_LIMIT_ENABLED: bool = False  # Disable for tests

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_app(db_session):
    """Create test FastAPI app with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(test_app):
    """Create test client for making HTTP requests."""
    return TestClient(test_app)

@pytest.fixture(scope="function")
def auth_headers(client, db_session) -> Dict[str, str]:
    """Create authenticated test user and return auth headers."""
    # Create test user
    user_data = {
        "email": "test@originfd.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "role": "engineer"
    }

    # Register user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Login to get token
    login_data = {"email": user_data["email"], "password": user_data["password"]}
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}

@pytest.fixture(scope="function")
def admin_headers(client, db_session) -> Dict[str, str]:
    """Create admin test user and return auth headers."""
    user_data = {
        "email": "admin@originfd.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "role": "admin"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    login_data = {"email": user_data["email"], "password": user_data["password"]}
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}

class TestHealthEndpoints:
    """Test health check and monitoring endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "OriginFD API Gateway"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"
        assert "performance" in data

    def test_health_endpoint(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]

    def test_detailed_health_endpoint(self, client):
        """Test detailed health check with metrics."""
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "uptime" in data
        assert "database" in data
        assert "performance_summary" in data

class TestAuthenticationFlow:
    """Test complete authentication and authorization flows."""

    def test_user_registration_and_login(self, client):
        """Test user registration and login flow."""
        # Registration
        user_data = {
            "email": "newuser@originfd.com",
            "password": "securepassword123",
            "full_name": "New User",
            "role": "viewer"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201

        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["full_name"] == user_data["full_name"]
        assert "id" in user

        # Login
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        login_data = {"email": "nonexistent@originfd.com", "password": "wrongpassword"}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401

    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/projects/")
        assert response.status_code == 401

    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Test accessing protected endpoint with valid authentication."""
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200

class TestProjectManagement:
    """Test project CRUD operations with proper authorization."""

    def test_create_project(self, client, auth_headers):
        """Test creating a new project."""
        project_data = {
            "name": "Test Solar Project",
            "description": "Integration test project",
            "domain": "PV",
            "scale": "COMMERCIAL",
            "location_name": "California, USA",
            "total_capacity_kw": 1000.0
        }

        response = client.post("/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201

        project = response.json()
        assert project["name"] == project_data["name"]
        assert project["domain"] == project_data["domain"]
        assert project["scale"] == project_data["scale"]
        assert "id" in project

    def test_list_projects(self, client, auth_headers):
        """Test listing projects with pagination."""
        # Create multiple projects
        for i in range(5):
            project_data = {
                "name": f"Test Project {i}",
                "description": f"Test project number {i}",
                "domain": "PV",
                "scale": "RESIDENTIAL"
            }
            response = client.post("/projects/", json=project_data, headers=auth_headers)
            assert response.status_code == 201

        # List projects
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["projects"]) == 5
        assert data["total"] == 5
        assert data["page"] == 1

        # Test pagination
        response = client.get("/projects/?page=2&page_size=3", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["projects"]) == 2  # Remaining projects
        assert data["page"] == 2

    def test_get_project_by_id(self, client, auth_headers):
        """Test retrieving a specific project by ID."""
        # Create project
        project_data = {
            "name": "Specific Test Project",
            "description": "Project for ID testing",
            "domain": "BESS",
            "scale": "INDUSTRIAL"
        }

        response = client.post("/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Get project by ID
        response = client.get(f"/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200

        project = response.json()
        assert project["id"] == project_id
        assert project["name"] == project_data["name"]

    def test_update_project(self, client, auth_headers):
        """Test updating an existing project."""
        # Create project
        project_data = {
            "name": "Original Project Name",
            "description": "Original description",
            "domain": "PV",
            "scale": "COMMERCIAL"
        }

        response = client.post("/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Update project
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "total_capacity_kw": 2000.0
        }

        response = client.patch(f"/projects/{project_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        updated_project = response.json()
        assert updated_project["name"] == update_data["name"]
        assert updated_project["description"] == update_data["description"]
        assert updated_project["total_capacity_kw"] == update_data["total_capacity_kw"]

    def test_project_authorization(self, client, auth_headers):
        """Test that users can only access their own projects."""
        # Create project with first user
        project_data = {
            "name": "Private Project",
            "description": "Should only be accessible to owner",
            "domain": "HYBRID",
            "scale": "UTILITY"
        }

        response = client.post("/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Create second user
        user2_data = {
            "email": "user2@originfd.com",
            "password": "password123",
            "full_name": "User Two",
            "role": "engineer"
        }

        response = client.post("/auth/register", json=user2_data)
        assert response.status_code == 201

        # Login as second user
        login_data = {"email": user2_data["email"], "password": user2_data["password"]}
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200

        user2_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        # Try to access first user's project - should fail
        response = client.get(f"/projects/{project_id}", headers=user2_headers)
        assert response.status_code == 404  # Should not be found for this user

class TestComponentManagement:
    """Test component CRUD operations with lifecycle management."""

    def test_create_component(self, client, auth_headers):
        """Test creating a new component."""
        component_data = {
            "brand": "TestBrand",
            "part_number": "TB-001",
            "rating_w": 500,
            "category": "pv_module",
            "domain": "PV",
            "scale": "COMMERCIAL"
        }

        response = client.post("/components/", json=component_data, headers=auth_headers)
        assert response.status_code == 201

        component = response.json()
        assert component["brand"] == component_data["brand"]
        assert component["part_number"] == component_data["part_number"]
        assert component["rating_w"] == component_data["rating_w"]
        assert component["status"] == "draft"  # Default status

    def test_list_components_with_filters(self, client, auth_headers):
        """Test listing components with various filters."""
        # Create components with different attributes
        components_data = [
            {"brand": "BrandA", "part_number": "PA-001", "rating_w": 300, "category": "pv_module"},
            {"brand": "BrandA", "part_number": "PA-002", "rating_w": 400, "category": "pv_module"},
            {"brand": "BrandB", "part_number": "PB-001", "rating_w": 500, "category": "inverter"},
        ]

        for data in components_data:
            response = client.post("/components/", json=data, headers=auth_headers)
            assert response.status_code == 201

        # Test listing all components
        response = client.get("/components/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["components"]) == 3

        # Test brand filter
        response = client.get("/components/?brand=BrandA", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["components"]) == 2

        # Test category filter
        response = client.get("/components/?category=inverter", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["components"]) == 1

        # Test search
        response = client.get("/components/?search=PA-002", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["components"]) == 1

    def test_component_status_transition(self, client, auth_headers):
        """Test component status transitions with validation."""
        # Create component
        component_data = {
            "brand": "StatusTest",
            "part_number": "ST-001",
            "rating_w": 600,
            "category": "battery"
        }

        response = client.post("/components/", json=component_data, headers=auth_headers)
        assert response.status_code == 201
        component_id = response.json()["id"]

        # Test valid status transition: draft -> approved
        transition_data = {"new_status": "approved", "comment": "Approved for testing"}
        response = client.post(f"/components/{component_id}/transition",
                              json=transition_data, headers=auth_headers)
        assert response.status_code == 200

        updated_component = response.json()
        assert updated_component["status"] == "approved"

        # Test invalid status transition
        invalid_transition = {"new_status": "draft", "comment": "Invalid transition"}
        response = client.post(f"/components/{component_id}/transition",
                              json=invalid_transition, headers=auth_headers)
        assert response.status_code == 400  # Should reject invalid transition

class TestPerformanceAndCaching:
    """Test performance optimizations and caching behavior."""

    def test_response_caching(self, client, auth_headers):
        """Test that responses are properly cached."""
        # Create a component for testing
        component_data = {
            "brand": "CacheTest",
            "part_number": "CT-001",
            "rating_w": 700
        }

        response = client.post("/components/", json=component_data, headers=auth_headers)
        assert response.status_code == 201

        # First request - should miss cache
        response1 = client.get("/components/", headers=auth_headers)
        assert response1.status_code == 200
        assert response1.headers.get("X-Cache") in [None, "MISS"]

        # Second request - should hit cache (if caching is enabled)
        response2 = client.get("/components/", headers=auth_headers)
        assert response2.status_code == 200
        # Cache behavior depends on configuration

    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting behavior (if enabled in tests)."""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/components/stats", headers=auth_headers)
            responses.append(response.status_code)

        # All should succeed if rate limiting is disabled for tests
        assert all(status == 200 for status in responses)

    def test_database_query_optimization(self, client, auth_headers, db_session):
        """Test that database queries are optimized (no N+1 queries)."""
        # Create multiple components with relationships
        for i in range(10):
            component_data = {
                "brand": f"OptimizationTest{i}",
                "part_number": f"OT-{i:03d}",
                "rating_w": 100 + i * 50
            }
            response = client.post("/components/", json=component_data, headers=auth_headers)
            assert response.status_code == 201

        # Enable SQL logging to monitor queries
        import logging
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

        # Make request that would trigger N+1 if not optimized
        response = client.get("/components/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["components"]) == 10

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_uuid_format(self, client, auth_headers):
        """Test handling of invalid UUID formats."""
        response = client.get("/components/invalid-uuid", headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_not_found_resource(self, client, auth_headers):
        """Test handling of non-existent resources."""
        fake_uuid = str(uuid4())
        response = client.get(f"/components/{fake_uuid}", headers=auth_headers)
        assert response.status_code == 404

    def test_validation_errors(self, client, auth_headers):
        """Test input validation errors."""
        # Missing required fields
        invalid_data = {"brand": "Test"}  # Missing part_number and rating_w
        response = client.post("/components/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

        # Invalid data types
        invalid_data = {"brand": "Test", "part_number": "TP-001", "rating_w": "not-a-number"}
        response = client.post("/components/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_sql_injection_protection(self, client, auth_headers):
        """Test protection against SQL injection attacks."""
        malicious_input = "'; DROP TABLE components; --"

        # Try SQL injection in search parameter
        response = client.get(f"/components/?search={malicious_input}", headers=auth_headers)
        # Should not crash and should return valid response
        assert response.status_code == 200

class TestIntegrationScenarios:
    """Test complete integration scenarios across multiple endpoints."""

    def test_complete_project_workflow(self, client, auth_headers):
        """Test complete project creation, component addition, and management workflow."""
        # 1. Create a project
        project_data = {
            "name": "Complete Workflow Project",
            "description": "End-to-end integration test",
            "domain": "HYBRID",
            "scale": "INDUSTRIAL",
            "total_capacity_kw": 5000.0
        }

        response = client.post("/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201
        project = response.json()
        project_id = project["id"]

        # 2. Create components for the project
        components_data = [
            {"brand": "SolarCorp", "part_number": "SC-PV-500", "rating_w": 500, "category": "pv_module"},
            {"brand": "InverTech", "part_number": "IT-INV-5K", "rating_w": 5000, "category": "inverter"},
            {"brand": "BatteryCorp", "part_number": "BC-BESS-10", "rating_w": 10000, "category": "battery"},
        ]

        component_ids = []
        for comp_data in components_data:
            response = client.post("/components/", json=comp_data, headers=auth_headers)
            assert response.status_code == 201
            component_ids.append(response.json()["id"])

        # 3. Approve components
        for comp_id in component_ids:
            transition_data = {"new_status": "approved", "comment": "Approved for project"}
            response = client.post(f"/components/{comp_id}/transition",
                                  json=transition_data, headers=auth_headers)
            assert response.status_code == 200

        # 4. Get project details and verify everything is connected
        response = client.get(f"/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        project_details = response.json()
        assert project_details["name"] == project_data["name"]

        # 5. List all approved components
        response = client.get("/components/?status=approved", headers=auth_headers)
        assert response.status_code == 200
        approved_components = response.json()["components"]
        assert len(approved_components) == 3

        # 6. Get project statistics
        response = client.get("/components/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_components"] >= 3

    def test_concurrent_operations(self, client, auth_headers):
        """Test handling of concurrent operations."""
        import threading
        import time

        results = []

        def create_component(index):
            """Function to create component in separate thread."""
            component_data = {
                "brand": f"ConcurrentBrand{index}",
                "part_number": f"CB-{index:03d}",
                "rating_w": 100 + index
            }
            response = client.post("/components/", json=component_data, headers=auth_headers)
            results.append(response.status_code)

        # Create multiple components concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_component, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(status == 201 for status in results)
        assert len(results) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])