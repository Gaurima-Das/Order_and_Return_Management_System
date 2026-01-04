from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import os
import uuid

from app.models.invoice import Invoice, InvoiceType
from app.models.order import Order
from app.models.return_model import Return


class InvoiceStorageService:
    """Service for storing and retrieving invoice records."""
    
    @staticmethod
    def generate_invoice_number(invoice_type: InvoiceType, reference_number: str) -> str:
        """Generate unique invoice number."""
        date_str = datetime.now().strftime('%Y%m%d')
        short_id = uuid.uuid4().hex[:6].upper()
        prefix = "INV" if invoice_type == InvoiceType.ORDER else "CM"
        return f"{prefix}-{date_str}-{short_id}"
    
    @staticmethod
    async def create_invoice_record(
        db: AsyncSession,
        invoice_type: InvoiceType,
        file_path: str,
        file_name: str,
        order_id: Optional[int] = None,
        return_id: Optional[int] = None,
    ) -> Invoice:
        """Create an invoice record in the database."""
        # Get reference number for invoice number generation
        if invoice_type == InvoiceType.ORDER and order_id:
            order_result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = order_result.scalar_one_or_none()
            reference = order.order_number if order else f"ORD-{order_id}"
        elif invoice_type == InvoiceType.RETURN and return_id:
            return_result = await db.execute(
                select(Return).where(Return.id == return_id)
            )
            return_obj = return_result.scalar_one_or_none()
            reference = return_obj.return_number if return_obj else f"RET-{return_id}"
        else:
            reference = "UNKNOWN"
        
        # Get file size
        file_size = None
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        invoice = Invoice(
            invoice_number=InvoiceStorageService.generate_invoice_number(invoice_type, reference),
            invoice_type=invoice_type,
            order_id=order_id,
            return_id=return_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
        )
        
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice
    
    @staticmethod
    async def get_invoice(db: AsyncSession, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID."""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_invoices_by_order(db: AsyncSession, order_id: int):
        """Get all invoices for an order."""
        result = await db.execute(
            select(Invoice).where(Invoice.order_id == order_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_invoices_by_return(db: AsyncSession, return_id: int):
        """Get all invoices for a return."""
        result = await db.execute(
            select(Invoice).where(Invoice.return_id == return_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    def create_invoice_record_sync(
        db_session,
        invoice_type: InvoiceType,
        file_path: str,
        file_name: str,
        order_id: Optional[int] = None,
        return_id: Optional[int] = None,
    ) -> Invoice:
        """Create an invoice record in the database (synchronous version for Celery)."""
        # Get reference number for invoice number generation
        reference = "UNKNOWN"
        if invoice_type == InvoiceType.ORDER and order_id:
            order = db_session.query(Order).filter(Order.id == order_id).first()
            reference = order.order_number if order else f"ORD-{order_id}"
        elif invoice_type == InvoiceType.RETURN and return_id:
            return_obj = db_session.query(Return).filter(Return.id == return_id).first()
            reference = return_obj.return_number if return_obj else f"RET-{return_id}"
        
        # Get file size
        file_size = None
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        invoice = Invoice(
            invoice_number=InvoiceStorageService.generate_invoice_number(invoice_type, reference),
            invoice_type=invoice_type,
            order_id=order_id,
            return_id=return_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
        )
        
        db_session.add(invoice)
        db_session.commit()
        db_session.refresh(invoice)
        return invoice

