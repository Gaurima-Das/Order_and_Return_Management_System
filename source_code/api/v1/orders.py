from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderStateUpdate
from app.services.order_service import OrderService

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new order.
    
    Required fields:
    - customer_id: integer
    - customer_email: valid email address
    - customer_name: string
    - items: array of order items (at least one)
      - product_id: integer
      - product_name: string
      - product_sku: string
      - unit_price: decimal/number
      - quantity: integer
    - shipping_address: object/dictionary
    - billing_address: object/dictionary
    
    Optional fields:
    - notes: string
    - meta_data: object/dictionary
    """
    try:
        # Validate items list is not empty
        if not order_data.items or len(order_data.items) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Items list cannot be empty. At least one item is required.",
            )
        
        order = await OrderService.create_order(db, order_data)
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[int] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List orders with optional filters."""
    orders = await OrderService.list_orders(
        db, skip=skip, limit=limit, customer_id=customer_id, status=status
    )
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get order by ID."""
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update order."""
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    
    order = await OrderService.update_order(db, order, order_update)
    return order


@router.post("/{order_id}/state", response_model=OrderResponse)
async def update_order_state(
    order_id: int,
    state_update: OrderStateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update order state (state machine transition)."""
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    
    try:
        order = await OrderService.transition_order_state(db, order, state_update.action)
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel an order."""
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    
    try:
        order = await OrderService.transition_order_state(db, order, "cancel")
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

