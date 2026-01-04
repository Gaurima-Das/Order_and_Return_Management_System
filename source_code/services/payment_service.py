from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.order import Order
from app.schemas.payment import PaymentCreate, PaymentUpdate, RefundRequest


class PaymentService:
    """Service for payment business logic."""
    
    @staticmethod
    def generate_payment_number() -> str:
        """Generate unique payment number."""
        return f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    async def create_payment(db: AsyncSession, payment_data: PaymentCreate) -> Payment:
        """Create a new payment."""
        # Verify order exists
        order_result = await db.execute(
            select(Order).where(Order.id == payment_data.order_id)
        )
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"Order {payment_data.order_id} not found")
        
        # Create payment
        payment = Payment(
            payment_number=PaymentService.generate_payment_number(),
            order_id=payment_data.order_id,
            status=PaymentStatus.PENDING,
            method=payment_data.method,
            amount=payment_data.amount,
            currency=payment_data.currency,
            transaction_id=payment_data.transaction_id,
            meta_data=payment_data.meta_data,
        )
        
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment
    
    @staticmethod
    async def get_payment(db: AsyncSession, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_payments(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_id: Optional[int] = None,
        status: Optional[PaymentStatus] = None,
    ) -> List[Payment]:
        """List payments with filters."""
        query = select(Payment)
        
        if order_id:
            query = query.where(Payment.order_id == order_id)
        if status:
            query = query.where(Payment.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_payment(
        db: AsyncSession,
        payment: Payment,
        payment_update: PaymentUpdate,
    ) -> Payment:
        """Update payment."""
        if payment_update.transaction_id is not None:
            payment.transaction_id = payment_update.transaction_id
        if payment_update.gateway_response is not None:
            payment.gateway_response = payment_update.gateway_response
        if payment_update.notes is not None:
            payment.notes = payment_update.notes
        if payment_update.meta_data is not None:
            payment.meta_data = payment_update.meta_data
        
        await db.commit()
        await db.refresh(payment)
        return payment
    
    @staticmethod
    async def process_payment(
        db: AsyncSession,
        payment: Payment,
    ) -> Payment:
        """Process payment (simulate payment gateway)."""
        # In real implementation, this would call payment gateway API
        # For now, we'll simulate success
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        payment.transaction_id = payment.transaction_id or f"TXN-{uuid.uuid4().hex[:16].upper()}"
        
        await db.commit()
        await db.refresh(payment)
        return payment
    
    @staticmethod
    async def process_refund(
        db: AsyncSession,
        payment: Payment,
        refund_request: RefundRequest,
    ) -> Payment:
        """Process refund."""
        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError(f"Payment {payment.id} is not completed and cannot be refunded")
        
        refund_amount = refund_request.amount or payment.amount
        
        if refund_amount > payment.amount - payment.refunded_amount:
            raise ValueError(f"Refund amount {refund_amount} exceeds available amount")
        
        payment.refunded_amount += refund_amount
        
        if payment.refunded_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED
        
        payment.refunded_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(payment)
        return payment

