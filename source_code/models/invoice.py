from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class InvoiceType(str, enum.Enum):
    """Invoice type enumeration."""
    ORDER = "order"
    RETURN = "return"


class Invoice(Base):
    """Invoice model for tracking generated PDF invoices."""
    
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    invoice_type = Column(Enum(InvoiceType), nullable=False, index=True)
    
    # References
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    return_id = Column(Integer, ForeignKey("returns.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="invoices")
    return_ = relationship("Return", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, type={self.invoice_type})>"

