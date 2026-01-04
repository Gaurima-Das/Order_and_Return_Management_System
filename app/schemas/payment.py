from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.payment import PaymentStatus, PaymentMethod


class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    order_id: int
    method: PaymentMethod
    amount: Decimal
    currency: str = "USD"
    transaction_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class RefundRequest(BaseModel):
    """Schema for refund request."""
    amount: Optional[Decimal] = Field(None, description="Partial refund amount. If None, full refund.")
    reason: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: int
    payment_number: str
    order_id: int
    status: PaymentStatus
    method: PaymentMethod
    amount: Decimal
    currency: str
    refunded_amount: Decimal
    transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

