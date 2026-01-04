"""
Unit tests for Payment API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.models.payment import PaymentStatus


@pytest.mark.asyncio
async def test_create_payment(client: TestClient, sample_order):
    """Test creating payment via API."""
    payment_data = {
        "order_id": sample_order.id,
        "method": "credit_card",
        "amount": 280.00,
        "currency": "USD"
    }
    response = client.post("/api/v1/payments", json=payment_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_payments(client: TestClient, sample_payment):
    """Test listing payments via API."""
    response = client.get("/api/v1/payments")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_payment(client: TestClient, sample_payment):
    """Test getting payment via API."""
    response = client.get(f"/api/v1/payments/{sample_payment.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_payment.id


@pytest.mark.asyncio
async def test_process_payment(client: TestClient, sample_payment):
    """Test processing payment via API."""
    response = client.post(f"/api/v1/payments/{sample_payment.id}/process")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_refund_payment(client: TestClient, sample_payment):
    """Test refunding payment via API."""
    # First process
    client.post(f"/api/v1/payments/{sample_payment.id}/process")
    
    # Then refund
    refund_data = {"amount": 100.00, "reason": "Test refund"}
    response = client.post(
        f"/api/v1/payments/{sample_payment.id}/refund",
        json=refund_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["refunded", "partially_refunded"]

