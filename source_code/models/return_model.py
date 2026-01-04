from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum

from app.database import Base


class ReturnStatus(str, enum.Enum):
    """Return status enumeration."""
    INITIATED = "initiated"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_SCHEDULED = "pickup_scheduled"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    PROCESSED = "processed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class ReturnReason(str, enum.Enum):
    """Return reason enumeration."""
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    DAMAGED = "damaged"
    SIZE_ISSUE = "size_issue"
    CHANGE_OF_MIND = "change_of_mind"
    OTHER = "other"


class Return(Base):
    """Return model representing a product return."""
    
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status and state
    status = Column(Enum(ReturnStatus), default=ReturnStatus.INITIATED, nullable=False, index=True)
    previous_status = Column(Enum(ReturnStatus), nullable=True)
    
    # Return information
    reason = Column(Enum(ReturnReason), nullable=False)
    reason_description = Column(Text, nullable=True)
    
    # Financial information
    refund_amount = Column(Numeric(10, 2), nullable=False)
    refund_method = Column(String(50), nullable=True)  # original_payment, store_credit, etc.
    currency = Column(String(3), default="USD")
    
    # Shipping information
    return_address = Column(JSON, nullable=True)
    tracking_number = Column(String(100), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    pickup_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="returns")
    items = relationship("ReturnItem", back_populates="return_", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="return_")
    
    def __repr__(self):
        return f"<Return(id={self.id}, return_number={self.return_number}, status={self.status})>"


class ReturnItem(Base):
    """Return item model representing a product in a return."""
    
    __tablename__ = "return_items"
    
    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("returns.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    
    # Product information
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=False)
    
    # Return information
    quantity = Column(Integer, nullable=False)
    refund_amount = Column(Numeric(10, 2), nullable=False)
    
    # Condition
    condition = Column(String(50), nullable=True)  # new, used, damaged, etc.
    condition_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    return_ = relationship("Return", back_populates="items")
    
    def __repr__(self):
        return f"<ReturnItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"

