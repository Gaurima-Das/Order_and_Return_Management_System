"""
Unit tests for Return Service.
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.return_service import ReturnService
from app.models.return_model import Return, ReturnStatus, ReturnReason
from app.schemas.return_schema import ReturnCreate, ReturnUpdate


@pytest.mark.asyncio
async def test_generate_return_number():
    """Test return number generation."""
    return_number = ReturnService.generate_return_number()
    assert return_number.startswith("RET-")
    assert len(return_number) > 10


@pytest.mark.asyncio
async def test_create_return(async_db_session: AsyncSession, sample_order, sample_return_data):
    """Test creating a new return."""
    # Set order to delivered status
    sample_order.status = OrderStatus.DELIVERED
    await async_db_session.commit()
    await async_db_session.refresh(sample_order)
    
    return_data = ReturnCreate(**sample_return_data)
    return_obj = await ReturnService.create_return(async_db_session, return_data)
    
    assert return_obj.id is not None
    assert return_obj.return_number.startswith("RET-")
    assert return_obj.status == ReturnStatus.INITIATED
    assert return_obj.order_id == sample_order.id
    assert len(return_obj.items) == 1


@pytest.mark.asyncio
async def test_create_return_invalid_order(async_db_session: AsyncSession, sample_return_data):
    """Test creating return for non-existent order."""
    sample_return_data["order_id"] = 99999
    return_data = ReturnCreate(**sample_return_data)
    
    with pytest.raises(ValueError, match="Order.*not found"):
        await ReturnService.create_return(async_db_session, return_data)


@pytest.mark.asyncio
async def test_get_return(async_db_session: AsyncSession, sample_return):
    """Test getting a return by ID."""
    return_obj = await ReturnService.get_return(async_db_session, sample_return.id)
    
    assert return_obj is not None
    assert return_obj.id == sample_return.id
    assert return_obj.return_number == sample_return.return_number
    assert len(return_obj.items) > 0


@pytest.mark.asyncio
async def test_list_returns(async_db_session: AsyncSession, sample_return):
    """Test listing returns."""
    returns = await ReturnService.list_returns(async_db_session)
    
    assert len(returns) >= 1
    assert any(r.id == sample_return.id for r in returns)


@pytest.mark.asyncio
async def test_transition_return_state_approve(async_db_session: AsyncSession, sample_return):
    """Test approving a return."""
    return_obj = await ReturnService.transition_return_state(
        async_db_session,
        sample_return,
        "approve"
    )
    
    assert return_obj.status == ReturnStatus.APPROVED
    assert return_obj.approved_at is not None


@pytest.mark.asyncio
async def test_transition_return_state_process(async_db_session: AsyncSession, sample_return):
    """Test processing a return (should trigger credit memo generation)."""
    # Go through full workflow
    await ReturnService.transition_return_state(async_db_session, sample_return, "approve")
    await async_db_session.refresh(sample_return)
    
    await ReturnService.transition_return_state(async_db_session, sample_return, "schedule_pickup")
    await async_db_session.refresh(sample_return)
    
    await ReturnService.transition_return_state(async_db_session, sample_return, "start_transit")
    await async_db_session.refresh(sample_return)
    
    await ReturnService.transition_return_state(async_db_session, sample_return, "receive")
    await async_db_session.refresh(sample_return)
    
    # Process (should trigger credit memo)
    return_obj = await ReturnService.transition_return_state(
        async_db_session,
        sample_return,
        "process"
    )
    
    assert return_obj.status == ReturnStatus.PROCESSED
    assert return_obj.processed_at is not None


@pytest.mark.asyncio
async def test_transition_return_state_invalid(async_db_session: AsyncSession, sample_return):
    """Test invalid state transition."""
    with pytest.raises(ValueError):
        await ReturnService.transition_return_state(
            async_db_session,
            sample_return,
            "process"  # Cannot process from INITIATED
        )


@pytest.mark.asyncio
async def test_transition_return_state_reject(async_db_session: AsyncSession, sample_return):
    """Test rejecting a return."""
    return_obj = await ReturnService.transition_return_state(
        async_db_session,
        sample_return,
        "reject",
        reason="Not eligible for return"
    )
    
    assert return_obj.status == ReturnStatus.REJECTED
    assert return_obj.rejection_reason == "Not eligible for return"

