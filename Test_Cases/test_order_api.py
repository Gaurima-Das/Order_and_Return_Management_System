"""
Unit tests for Order API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_create_order(client: TestClient, sample_order_data):
    """Test creating order via API."""
    response = client.post("/api/v1/orders", json=sample_order_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "order_number" in data
    assert data["status"] == "pending"
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_create_order_empty_items(client: TestClient, sample_order_data):
    """Test creating order with empty items list."""
    sample_order_data["items"] = []
    response = client.post("/api/v1/orders", json=sample_order_data)
    
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_orders(client: TestClient, sample_order):
    """Test listing orders via API."""
    response = client.get("/api/v1/orders")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_order(client: TestClient, sample_order):
    """Test getting order via API."""
    response = client.get(f"/api/v1/orders/{sample_order.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_order.id
    assert "items" in data


@pytest.mark.asyncio
async def test_get_order_not_found(client: TestClient):
    """Test getting non-existent order."""
    response = client.get("/api/v1/orders/99999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_order_state(client: TestClient, sample_order):
    """Test updating order state via API."""
    # First confirm
    response = client.post(
        f"/api/v1/orders/{sample_order.id}/state",
        json={"action": "confirm"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_update_order_state_invalid(client: TestClient, sample_order):
    """Test invalid state transition via API."""
    response = client.post(
        f"/api/v1/orders/{sample_order.id}/state",
        json={"action": "ship"}  # Cannot ship from pending
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_order(client: TestClient, sample_order):
    """Test cancelling order via API."""
    response = client.post(f"/api/v1/orders/{sample_order.id}/cancel")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"

