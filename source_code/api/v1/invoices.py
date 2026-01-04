from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pathlib import Path

from app.database import get_db
from app.schemas.invoice import InvoiceResponse
from app.services.invoice_storage_service import InvoiceStorageService

router = APIRouter()


@router.get("/order/{order_id}", response_model=List[InvoiceResponse])
async def get_order_invoices(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all invoices for an order."""
    invoices = await InvoiceStorageService.get_invoices_by_order(db, order_id)
    return invoices


@router.get("/return/{return_id}", response_model=List[InvoiceResponse])
async def get_return_invoices(
    return_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all invoices (credit memos) for a return."""
    invoices = await InvoiceStorageService.get_invoices_by_return(db, return_id)
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get invoice details by ID."""
    invoice = await InvoiceStorageService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    return invoice


@router.get("/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Download invoice PDF file."""
    invoice = await InvoiceStorageService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    file_path = Path(invoice.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice file not found: {invoice.file_path}",
        )
    
    return FileResponse(
        path=str(file_path),
        filename=invoice.file_name,
        media_type="application/pdf",
    )

