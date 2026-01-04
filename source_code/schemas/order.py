from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """Schema for creating an order item."""
    product_id: int
    product_name: str
    product_sku: str
    unit_price: Decimal
    quantity: int
    meta_data: Optional[Dict[str, Any]] = None


class OrderItemResponse(BaseModel):
    """Schema for order item response."""
    id: int
    product_id: int
    product_name: str
    product_sku: str
    unit_price: Decimal
    quantity: int
    total_price: Decimal
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    customer_id: int
    customer_email: EmailStr
    customer_name: str
    items: List[OrderItemCreate]
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class OrderStateUpdate(BaseModel):
    """Schema for updating order state."""
    action: str = Field(..., description="State transition action (e.g., 'confirm', 'ship', 'cancel')")
    meta_data: Optional[Dict[str, Any]] = None


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: int
    order_number: str
    customer_id: int
    customer_email: str
    customer_name: str
    status: OrderStatus
    previous_status: Optional[OrderStatus] = None
    subtotal: Decimal
    tax: Decimal
    shipping_cost: Decimal
    total: Decimal
    currency: str
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    notes: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

