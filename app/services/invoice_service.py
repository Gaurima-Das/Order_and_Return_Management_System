from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.models.order import Order, OrderItem
from app.models.return_model import Return, ReturnItem


class InvoiceService:
    """Service for generating PDF invoices."""
    
    # Create invoices directory if it doesn't exist
    INVOICES_DIR = Path("invoices")
    INVOICES_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def generate_order_invoice(order: Order) -> str:
        """
        Generate PDF invoice for an order.
        Returns the file path of the generated invoice.
        """
        # Generate filename
        filename = f"invoice_order_{order.order_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = InvoiceService.INVOICES_DIR / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        # Title
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Invoice details
        invoice_data = [
            ['Invoice Number:', order.order_number],
            ['Invoice Date:', order.created_at.strftime('%B %d, %Y') if order.created_at else 'N/A'],
            ['Order Date:', order.created_at.strftime('%B %d, %Y') if order.created_at else 'N/A'],
        ]
        
        if order.shipped_at:
            invoice_data.append(['Shipped Date:', order.shipped_at.strftime('%B %d, %Y')])
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Customer and Shipping Information
        info_data = [
            ['Bill To:', 'Ship To:'],
            [
                f"{order.customer_name}<br/>{order.customer_email}",
                f"{order.customer_name}<br/>{order.shipping_address.get('street', '')}<br/>{order.shipping_address.get('city', '')}, {order.shipping_address.get('state', '')} {order.shipping_address.get('zip', '')}"
            ]
        ]
        
        info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Items table
        elements.append(Paragraph("Order Items", heading_style))
        
        items_data = [['Product', 'SKU', 'Quantity', 'Unit Price', 'Total']]
        
        for item in order.items:
            items_data.append([
                item.product_name,
                item.product_sku,
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.total_price:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"${order.subtotal:.2f}"],
            ['Tax:', f"${order.tax:.2f}"],
            ['Shipping:', f"${order.shipping_cost:.2f}"],
            ['', ''],
            ['<b>TOTAL:</b>', f"<b>${order.total:.2f}</b>"],
        ]
        
        totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.grey),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = "Thank you for your business!"
        elements.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceBefore=20,
        )))
        
        # Build PDF
        doc.build(elements)
        
        return str(filepath)
    
    @staticmethod
    def generate_return_invoice(return_obj: Return) -> str:
        """
        Generate PDF invoice/credit memo for a return.
        Returns the file path of the generated invoice.
        """
        # Generate filename
        filename = f"credit_memo_return_{return_obj.return_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = InvoiceService.INVOICES_DIR / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        # Title
        elements.append(Paragraph("CREDIT MEMO", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Return details
        return_data = [
            ['Credit Memo Number:', return_obj.return_number],
            ['Return Date:', return_obj.created_at.strftime('%B %d, %Y') if return_obj.created_at else 'N/A'],
            ['Original Order:', f"Order #{return_obj.order.order_number}" if return_obj.order else 'N/A'],
            ['Return Reason:', return_obj.reason.value.replace('_', ' ').title()],
        ]
        
        if return_obj.processed_at:
            return_data.append(['Processed Date:', return_obj.processed_at.strftime('%B %d, %Y')])
        if return_obj.refunded_at:
            return_data.append(['Refunded Date:', return_obj.refunded_at.strftime('%B %d, %Y')])
        
        return_table = Table(return_data, colWidths=[2*inch, 4*inch])
        return_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(return_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Customer Information
        if return_obj.order:
            customer_info = f"Customer: {return_obj.order.customer_name}<br/>Email: {return_obj.order.customer_email}"
            elements.append(Paragraph(customer_info, normal_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Return items table
        elements.append(Paragraph("Returned Items", heading_style))
        
        items_data = [['Product', 'SKU', 'Quantity', 'Refund Amount']]
        
        for item in return_obj.items:
            items_data.append([
                item.product_name,
                item.product_sku,
                str(item.quantity),
                f"${item.refund_amount:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 1.5*inch, 1*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Refund total
        totals_data = [
            ['', ''],
            ['<b>Total Refund Amount:</b>', f"<b>${return_obj.refund_amount:.2f}</b>"],
        ]
        
        if return_obj.refund_method:
            totals_data.insert(0, ['Refund Method:', return_obj.refund_method.replace('_', ' ').title()])
        
        totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.grey),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = "This credit memo has been processed and refunded."
        elements.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceBefore=20,
        )))
        
        # Build PDF
        doc.build(elements)
        
        return str(filepath)

