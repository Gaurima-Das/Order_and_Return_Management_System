"""
Unit tests for Return API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.models.order import OrderStatus


@pytest.mark.asyncio
async def test_create_return(client: TestClient, sample_order, sample_return_data, async_db_session):
    """Test creating return via API."""
    # Set order to delivered
    sample_order.status = OrderStatus.DELIVERED
    await async_db_session.commit()
    await async_db_session.refresh(sample_order)
    
    response = client.post("/api/v1/returns", json=sample_return_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "return_number" in data
    assert data["status"] == "initiated"


@pytest.mark.asyncio
async def test_list_returns(client: TestClient, sample_return):
    """Test listing returns via API."""
    response = client.get("/api/v1/returns")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_return(client: TestClient, sample_return):
    """Test getting return via API."""
    response = client.get(f"/api/v1/returns/{sample_return.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_return.id


@pytest.mark.asyncio
async def test_update_return_state(client: TestClient, sample_return):
    """Test updating return state via API."""
    response = client.post(
        f"/api/v1/returns/{sample_return.id}/state",
        json={"action": "approve"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_approve_return(client: TestClient, sample_return):
    """Test approving return via API."""
    response = client.post(f"/api/v1/returns/{sample_return.id}/approve")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_return(client: TestClient, sample_return):
    """Test rejecting return via API."""
    response = client.post(
        f"/api/v1/returns/{sample_return.id}/reject",
        params={"reason": "Not eligible"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"

