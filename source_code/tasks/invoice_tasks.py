from celery import shared_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config import settings
from app.models.order import Order
from app.models.return_model import Return
from app.models.invoice import InvoiceType
from app.services.invoice_service import InvoiceService
from app.services.invoice_storage_service import InvoiceStorageService
import logging

logger = logging.getLogger(__name__)

# Create synchronous database session for Celery tasks
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@shared_task(name="generate_order_invoice")
def generate_order_invoice(order_id: int):
    """
    Background task to generate PDF invoice when order is shipped.
    
    Args:
        order_id: ID of the order to generate invoice for
    """
    logger.info(f"=== Starting invoice generation for order {order_id} ===")
    db = SessionLocal()
    try:
        # Load order with items relationship (using sync query for Celery)
        from sqlalchemy.orm import joinedload
        logger.info(f"Loading order {order_id} from database...")
        order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
        
        if not order:
            logger.error(f"Order {order_id} not found for invoice generation")
            return {"status": "error", "error": f"Order {order_id} not found"}
        
        logger.info(f"Order found: {order.order_number}, Status: {order.status.value}, Items: {len(order.items)}")
        
        if order.status.value != "shipped":
            logger.warning(f"Order {order_id} is not in shipped state (current: {order.status.value})")
            return {"status": "skipped", "reason": f"Order not in shipped state"}
        
        # Generate invoice
        logger.info(f"Generating invoice PDF for order {order.order_number}...")
        invoice_path = InvoiceService.generate_order_invoice(order)
        logger.info(f"Invoice PDF generated at: {invoice_path}")
        filename = invoice_path.split("/")[-1] if "/" in invoice_path else invoice_path.split("\\")[-1]
        
        # Save invoice record to database (using sync method for Celery)
        invoice = InvoiceStorageService.create_invoice_record_sync(
            db_session=db,
            invoice_type=InvoiceType.ORDER,
            file_path=invoice_path,
            file_name=filename,
            order_id=order_id,
        )
        
        logger.info(f"Invoice generated for order {order.order_number}: {invoice_path} (Invoice #{invoice.invoice_number})")
        logger.info(f"=== Invoice generation completed successfully for order {order_id} ===")
        
        return {
            "status": "success",
            "order_id": order_id,
            "order_number": order.order_number,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_path": invoice_path,
            "filename": filename
        }
    except Exception as e:
        logger.error(f"=== ERROR generating invoice for order {order_id} ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
        logger.info(f"Database session closed for order {order_id}")


@shared_task(name="generate_return_invoice")
def generate_return_invoice(return_id: int):
    """
    Background task to generate PDF credit memo when return is processed/completed.
    
    Args:
        return_id: ID of the return to generate invoice for
    """
    logger.info(f"=== Starting credit memo generation for return {return_id} ===")
    db = SessionLocal()
    try:
        # Load return with items and order relationship (using sync query for Celery)
        from sqlalchemy.orm import joinedload
        logger.info(f"Loading return {return_id} from database...")
        return_obj = db.query(Return).options(
            joinedload(Return.items), 
            joinedload(Return.order)
        ).filter(Return.id == return_id).first()
        
        if not return_obj:
            logger.error(f"Return {return_id} not found for invoice generation")
            return {"status": "error", "error": f"Return {return_id} not found"}
        
        logger.info(f"Return found: {return_obj.return_number}, Status: {return_obj.status.value}, Items: {len(return_obj.items)}")
        
        # Check if return is in a completed state (processed or refunded)
        if return_obj.status.value not in ["processed", "refunded"]:
            logger.warning(f"Return {return_id} is not in completed state (current: {return_obj.status.value})")
            return {"status": "skipped", "reason": f"Return not in completed state"}
        
        # Generate credit memo/invoice
        logger.info(f"Generating credit memo PDF for return {return_obj.return_number}...")
        invoice_path = InvoiceService.generate_return_invoice(return_obj)
        logger.info(f"Credit memo PDF generated at: {invoice_path}")
        filename = invoice_path.split("/")[-1] if "/" in invoice_path else invoice_path.split("\\")[-1]
        
        # Save invoice record to database (using sync method for Celery)
        invoice = InvoiceStorageService.create_invoice_record_sync(
            db_session=db,
            invoice_type=InvoiceType.RETURN,
            file_path=invoice_path,
            file_name=filename,
            return_id=return_id,
        )
        
        logger.info(f"Credit memo generated for return {return_obj.return_number}: {invoice_path} (Invoice #{invoice.invoice_number})")
        logger.info(f"=== Credit memo generation completed successfully for return {return_id} ===")
        
        return {
            "status": "success",
            "return_id": return_id,
            "return_number": return_obj.return_number,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_path": invoice_path,
            "filename": filename
        }
    except Exception as e:
        logger.error(f"=== ERROR generating credit memo for return {return_id} ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
        logger.info(f"Database session closed for return {return_id}")

