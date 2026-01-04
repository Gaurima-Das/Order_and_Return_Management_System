"""
Unit tests for Order Service.
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.order_service import OrderService
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


@pytest.mark.asyncio
async def test_generate_order_number():
    """Test order number generation."""
    order_number = OrderService.generate_order_number()
    assert order_number.startswith("ORD-")
    assert len(order_number) > 10


@pytest.mark.asyncio
async def test_create_order(async_db_session: AsyncSession, sample_order_data):
    """Test creating a new order."""
    order_data = OrderCreate(**sample_order_data)
    order = await OrderService.create_order(async_db_session, order_data)
    
    assert order.id is not None
    assert order.order_number.startswith("ORD-")
    assert order.status == OrderStatus.PENDING
    assert order.customer_email == sample_order_data["customer_email"]
    assert len(order.items) == 2
    assert order.total == Decimal("280.00")  # 250 + 25 (tax) + 5 (shipping)


@pytest.mark.asyncio
async def test_create_order_with_empty_items(async_db_session: AsyncSession, sample_order_data):
    """Test creating order with empty items list should fail."""
    sample_order_data["items"] = []
    order_data = OrderCreate(**sample_order_data)
    
    with pytest.raises(ValueError):
        await OrderService.create_order(async_db_session, order_data)


@pytest.mark.asyncio
async def test_get_order(async_db_session: AsyncSession, sample_order):
    """Test getting an order by ID."""
    order = await OrderService.get_order(async_db_session, sample_order.id)
    
    assert order is not None
    assert order.id == sample_order.id
    assert order.order_number == sample_order.order_number
    assert len(order.items) > 0


@pytest.mark.asyncio
async def test_get_order_not_found(async_db_session: AsyncSession):
    """Test getting non-existent order."""
    order = await OrderService.get_order(async_db_session, 99999)
    assert order is None


@pytest.mark.asyncio
async def test_list_orders(async_db_session: AsyncSession, sample_order):
    """Test listing orders."""
    orders = await OrderService.list_orders(async_db_session)
    
    assert len(orders) >= 1
    assert any(o.id == sample_order.id for o in orders)


@pytest.mark.asyncio
async def test_list_orders_with_filters(async_db_session: AsyncSession, sample_order):
    """Test listing orders with filters."""
    # Filter by customer_id
    orders = await OrderService.list_orders(
        async_db_session,
        customer_id=sample_order.customer_id
    )
    assert len(orders) >= 1
    assert all(o.customer_id == sample_order.customer_id for o in orders)
    
    # Filter by status
    orders = await OrderService.list_orders(
        async_db_session,
        status=OrderStatus.PENDING
    )
    assert len(orders) >= 1
    assert all(o.status == OrderStatus.PENDING for o in orders)


@pytest.mark.asyncio
async def test_update_order(async_db_session: AsyncSession, sample_order):
    """Test updating an order."""
    update_data = OrderUpdate(notes="Updated notes", meta_data={"key": "value"})
    updated_order = await OrderService.update_order(
        async_db_session,
        sample_order,
        update_data
    )
    
    assert updated_order.notes == "Updated notes"
    assert updated_order.meta_data == {"key": "value"}


@pytest.mark.asyncio
async def test_transition_order_state_confirm(async_db_session: AsyncSession, sample_order):
    """Test transitioning order to confirmed state."""
    order = await OrderService.transition_order_state(
        async_db_session,
        sample_order,
        "confirm"
    )
    
    assert order.status == OrderStatus.CONFIRMED
    assert order.confirmed_at is not None


@pytest.mark.asyncio
async def test_transition_order_state_ship(async_db_session: AsyncSession, sample_order):
    """Test transitioning order to shipped state."""
    # First confirm and process
    await OrderService.transition_order_state(async_db_session, sample_order, "confirm")
    await async_db_session.refresh(sample_order)
    
    await OrderService.transition_order_state(async_db_session, sample_order, "start_processing")
    await async_db_session.refresh(sample_order)
    
    # Then ship
    order = await OrderService.transition_order_state(
        async_db_session,
        sample_order,
        "ship"
    )
    
    assert order.status == OrderStatus.SHIPPED
    assert order.shipped_at is not None


@pytest.mark.asyncio
async def test_transition_order_state_invalid(async_db_session: AsyncSession, sample_order):
    """Test invalid state transition."""
    with pytest.raises(ValueError):
        await OrderService.transition_order_state(
            async_db_session,
            sample_order,
            "ship"  # Cannot ship from PENDING
        )


@pytest.mark.asyncio
async def test_transition_order_state_already_in_state(async_db_session: AsyncSession, sample_order):
    """Test transitioning to same state."""
    # Confirm order
    await OrderService.transition_order_state(async_db_session, sample_order, "confirm")
    await async_db_session.refresh(sample_order)
    
    # Try to confirm again
    with pytest.raises(ValueError, match="already confirmed"):
        await OrderService.transition_order_state(
            async_db_session,
            sample_order,
            "confirm"
        )


@pytest.mark.asyncio
async def test_transition_order_state_cancel(async_db_session: AsyncSession, sample_order):
    """Test cancelling an order."""
    order = await OrderService.transition_order_state(
        async_db_session,
        sample_order,
        "cancel"
    )
    
    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at is not None

