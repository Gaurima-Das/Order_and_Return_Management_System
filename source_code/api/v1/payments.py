from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models.payment import PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse, RefundRequest
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new payment."""
    try:
        payment = await PaymentService.create_payment(db, payment_data)
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    order_id: Optional[int] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List payments with optional filters."""
    payments = await PaymentService.list_payments(
        db, skip=skip, limit=limit, order_id=order_id, status=status
    )
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payment by ID."""
    payment = await PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    return payment


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update payment."""
    payment = await PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    
    payment = await PaymentService.update_payment(db, payment, payment_update)
    return payment


@router.post("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Process a payment."""
    payment = await PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    
    try:
        payment = await PaymentService.process_payment(db, payment)
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: int,
    refund_request: RefundRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process a refund."""
    payment = await PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    
    try:
        payment = await PaymentService.process_refund(db, payment, refund_request)
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

