"""
Unit tests for Invoice API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.models.invoice import InvoiceType


@pytest.mark.asyncio
async def test_get_order_invoices(client: TestClient, sample_order, sample_invoice):
    """Test getting invoices for an order."""
    response = client.get(f"/api/v1/invoices/order/{sample_order.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_return_invoices(client: TestClient, sample_return, sample_invoice, async_db_session):
    """Test getting credit memos for a return."""
    # Update invoice to be for return
    sample_invoice.return_id = sample_return.id
    sample_invoice.order_id = None
    await async_db_session.commit()
    await async_db_session.refresh(sample_invoice)
    
    response = client.get(f"/api/v1/invoices/return/{sample_return.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_invoice(client: TestClient, sample_invoice):
    """Test getting invoice by ID."""
    response = client.get(f"/api/v1/invoices/{sample_invoice.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_invoice.id
    assert "invoice_number" in data


@pytest.mark.asyncio
async def test_get_invoice_not_found(client: TestClient):
    """Test getting non-existent invoice."""
    response = client.get("/api/v1/invoices/99999")
    
    assert response.status_code == 404

