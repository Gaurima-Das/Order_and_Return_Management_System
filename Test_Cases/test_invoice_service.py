"""
Unit tests for Invoice Service.
"""
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone

from app.services.invoice_service import InvoiceService
from app.models.order import Order, OrderItem, OrderStatus
from app.models.return_model import Return, ReturnItem, ReturnStatus, ReturnReason


def test_generate_order_invoice(db_session, sample_order):
    """Test generating order invoice PDF."""
    # Set order to shipped
    sample_order.status = OrderStatus.SHIPPED
    sample_order.shipped_at = datetime.now(timezone.utc)
    db_session.commit()
    
    invoice_path = InvoiceService.generate_order_invoice(sample_order)
    
    assert invoice_path is not None
    assert Path(invoice_path).exists()
    assert invoice_path.endswith(".pdf")
    assert "invoice_order" in invoice_path
    
    # Clean up
    Path(invoice_path).unlink(missing_ok=True)


def test_generate_return_invoice(sample_return, sample_order, db_session):
    """Test generating return credit memo PDF."""
    # Set return to processed
    sample_return.status = ReturnStatus.PROCESSED
    sample_return.processed_at = datetime.now(timezone.utc)
    sample_return.order = sample_order
    db_session.commit()
    
    invoice_path = InvoiceService.generate_return_invoice(sample_return)
    
    assert invoice_path is not None
    assert Path(invoice_path).exists()
    assert invoice_path.endswith(".pdf")
    assert "credit_memo_return" in invoice_path
    
    # Clean up
    Path(invoice_path).unlink(missing_ok=True)


def test_invoice_directory_creation():
    """Test that invoices directory is created."""
    assert InvoiceService.INVOICES_DIR.exists()
    assert InvoiceService.INVOICES_DIR.is_dir()

