from celery import shared_task
from typing import Dict, Any


@shared_task(name="send_order_confirmation_email")
def send_order_confirmation_email(order_id: int, customer_email: str, order_data: Dict[str, Any]):
    """
    Background task to send order confirmation email.
    In production, this would integrate with an email service like SendGrid, SES, etc.
    """
    try:
        # Simulate email sending
        print(f"Sending order confirmation email to {customer_email} for order {order_id}")
        # In production:
        # from app.services.email_service import send_email
        # send_email(
        #     to=customer_email,
        #     subject=f"Order Confirmation - {order_data['order_number']}",
        #     template="order_confirmation",
        #     context=order_data
        # )
        return {"status": "success", "order_id": order_id, "email": customer_email}
    except Exception as e:
        print(f"Error sending order confirmation email: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(name="send_order_shipment_notification")
def send_order_shipment_notification(order_id: int, customer_email: str, tracking_number: str):
    """
    Background task to send shipment notification email.
    """
    try:
        print(f"Sending shipment notification to {customer_email} for order {order_id} with tracking {tracking_number}")
        return {"status": "success", "order_id": order_id, "email": customer_email}
    except Exception as e:
        print(f"Error sending shipment notification: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(name="send_return_approval_notification")
def send_return_approval_notification(return_id: int, customer_email: str, return_data: Dict[str, Any]):
    """
    Background task to send return approval notification.
    """
    try:
        print(f"Sending return approval notification to {customer_email} for return {return_id}")
        return {"status": "success", "return_id": return_id, "email": customer_email}
    except Exception as e:
        print(f"Error sending return approval notification: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(name="send_refund_confirmation")
def send_refund_confirmation(return_id: int, customer_email: str, refund_amount: float):
    """
    Background task to send refund confirmation email.
    """
    try:
        print(f"Sending refund confirmation to {customer_email} for return {return_id}, amount: {refund_amount}")
        return {"status": "success", "return_id": return_id, "email": customer_email}
    except Exception as e:
        print(f"Error sending refund confirmation: {str(e)}")
        return {"status": "error", "error": str(e)}

