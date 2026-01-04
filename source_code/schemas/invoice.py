from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.invoice import InvoiceType


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    id: int
    invoice_number: str
    invoice_type: InvoiceType
    order_id: Optional[int] = None
    return_id: Optional[int] = None
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

