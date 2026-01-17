"""
Unit tests for FastAPI application endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns application metadata."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "name" in data
    assert "version" in data
    assert "maintainer" in data
    assert data["name"] == "Cloud-Native-Ops-Starter"


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    """Test health endpoint returns healthy status."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data


@pytest.mark.anyio
async def test_liveness_endpoint(client: AsyncClient):
    """Test liveness probe endpoint."""
    response = await client.get("/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.anyio
async def test_readiness_endpoint(client: AsyncClient):
    """Test readiness probe endpoint."""
    response = await client.get("/ready")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.anyio
async def test_system_status_endpoint(client: AsyncClient):
    """Test system status endpoint returns expected structure."""
    response = await client.get("/api/v1/system-status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify top-level keys
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "status" in data
    assert "metrics" in data
    assert "dependencies" in data
    
    # Verify nested structure
    assert "api_gateway" in data["status"]
    assert "uptime_seconds" in data["metrics"]
    assert "postgres" in data["dependencies"]


@pytest.mark.anyio
async def test_openapi_docs_available(client: AsyncClient):
    """Test OpenAPI documentation is accessible."""
    response = await client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
