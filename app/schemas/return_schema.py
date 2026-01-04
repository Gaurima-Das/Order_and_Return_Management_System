from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.return_model import ReturnStatus, ReturnReason


class ReturnItemCreate(BaseModel):
    """Schema for creating a return item."""
    order_item_id: int
    product_id: int
    product_name: str
    product_sku: str
    quantity: int
    condition: Optional[str] = None
    condition_notes: Optional[str] = None


class ReturnItemResponse(BaseModel):
    """Schema for return item response."""
    id: int
    order_item_id: int
    product_id: int
    product_name: str
    product_sku: str
    quantity: int
    refund_amount: Decimal
    condition: Optional[str] = None
    condition_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReturnCreate(BaseModel):
    """Schema for creating a return."""
    order_id: int
    reason: ReturnReason
    reason_description: Optional[str] = None
    items: List[ReturnItemCreate]
    return_address: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class ReturnUpdate(BaseModel):
    """Schema for updating a return."""
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class ReturnStateUpdate(BaseModel):
    """Schema for updating return state."""
    action: str = Field(..., description="State transition action (e.g., 'approve', 'reject', 'refund')")
    reason: Optional[str] = Field(None, description="Reason for rejection or other actions")
    meta_data: Optional[Dict[str, Any]] = None


class ReturnResponse(BaseModel):
    """Schema for return response."""
    id: int
    return_number: str
    order_id: int
    status: ReturnStatus
    previous_status: Optional[ReturnStatus] = None
    reason: ReturnReason
    reason_description: Optional[str] = None
    refund_amount: Decimal
    refund_method: Optional[str] = None
    currency: str
    return_address: Optional[Dict[str, Any]] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    items: List[ReturnItemResponse]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    pickup_scheduled_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

