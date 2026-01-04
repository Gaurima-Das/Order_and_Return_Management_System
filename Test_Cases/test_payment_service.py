"""
Unit tests for Payment Service.
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.payment_service import PaymentService
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.schemas.payment import PaymentCreate, PaymentUpdate, RefundRequest


@pytest.mark.asyncio
async def test_generate_payment_number():
    """Test payment number generation."""
    payment_number = PaymentService.generate_payment_number()
    assert payment_number.startswith("PAY-")
    assert len(payment_number) > 10


@pytest.mark.asyncio
async def test_create_payment(async_db_session: AsyncSession, sample_order):
    """Test creating a new payment."""
    payment_data = PaymentCreate(
        order_id=sample_order.id,
        method=PaymentMethod.CREDIT_CARD,
        amount=Decimal("280.00"),
        currency="USD"
    )
    payment = await PaymentService.create_payment(async_db_session, payment_data)
    
    assert payment.id is not None
    assert payment.payment_number.startswith("PAY-")
    assert payment.status == PaymentStatus.PENDING
    assert payment.order_id == sample_order.id


@pytest.mark.asyncio
async def test_get_payment(async_db_session: AsyncSession, sample_payment):
    """Test getting a payment by ID."""
    payment = await PaymentService.get_payment(async_db_session, sample_payment.id)
    
    assert payment is not None
    assert payment.id == sample_payment.id
    assert payment.payment_number == sample_payment.payment_number


@pytest.mark.asyncio
async def test_list_payments(async_db_session: AsyncSession, sample_payment):
    """Test listing payments."""
    payments = await PaymentService.list_payments(async_db_session)
    
    assert len(payments) >= 1
    assert any(p.id == sample_payment.id for p in payments)


@pytest.mark.asyncio
async def test_process_payment(async_db_session: AsyncSession, sample_payment):
    """Test processing a payment."""
    payment = await PaymentService.process_payment(async_db_session, sample_payment)
    
    assert payment.status == PaymentStatus.COMPLETED
    assert payment.completed_at is not None


@pytest.mark.asyncio
async def test_refund_payment_full(async_db_session: AsyncSession, sample_payment):
    """Test full refund."""
    # First process the payment
    await PaymentService.process_payment(async_db_session, sample_payment)
    await async_db_session.refresh(sample_payment)
    
    # Then refund
    refund_request = RefundRequest(amount=None)  # Full refund
    payment = await PaymentService.process_refund(
        async_db_session,
        sample_payment,
        refund_request
    )
    
    assert payment.status == PaymentStatus.REFUNDED
    assert payment.refunded_amount == sample_payment.amount
    assert payment.refunded_at is not None


@pytest.mark.asyncio
async def test_refund_payment_partial(async_db_session: AsyncSession, sample_payment):
    """Test partial refund."""
    # First process the payment
    await PaymentService.process_payment(async_db_session, sample_payment)
    await async_db_session.refresh(sample_payment)
    
    # Then partial refund
    refund_request = RefundRequest(amount=Decimal("100.00"))
    payment = await PaymentService.process_refund(
        async_db_session,
        sample_payment,
        refund_request
    )
    
    assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
    assert payment.refunded_amount == Decimal("100.00")

