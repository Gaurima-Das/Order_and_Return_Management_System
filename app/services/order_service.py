from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate
from app.state_machines.order_state import OrderStateMachine


class OrderService:
    """Service for order business logic."""
    
    @staticmethod
    def generate_order_number() -> str:
        """Generate unique order number."""
        return f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    async def create_order(db: AsyncSession, order_data: OrderCreate) -> Order:
        """Create a new order."""
        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in order_data.items)
        tax = subtotal * Decimal("0.10")  # 10% tax (adjust as needed)
        shipping_cost = Decimal("5.00")  # Fixed shipping (adjust as needed)
        total = subtotal + tax + shipping_cost
        
        # Create order
        order = Order(
            order_number=OrderService.generate_order_number(),
            customer_id=order_data.customer_id,
            customer_email=order_data.customer_email,
            customer_name=order_data.customer_name,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping_cost,
            total=total,
            shipping_address=order_data.shipping_address,
            billing_address=order_data.billing_address,
            notes=order_data.notes,
            meta_data=order_data.meta_data,
        )
        
        db.add(order)
        await db.flush()  # Get order ID
        
        # Create order items
        for item_data in order_data.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                product_sku=item_data.product_sku,
                unit_price=item_data.unit_price,
                quantity=item_data.quantity,
                total_price=item_data.unit_price * item_data.quantity,
                meta_data=item_data.meta_data,
            )
            db.add(order_item)
        
        await db.commit()
        # Reload order with relationships to avoid async loading issues
        return await OrderService.get_order(db, order.id)
    
    @staticmethod
    async def get_order(db: AsyncSession, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_order_by_number(db: AsyncSession, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        result = await db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_orders(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[Order]:
        """List orders with filters."""
        query = select(Order).options(selectinload(Order.items))
        
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        if status:
            query = query.where(Order.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_order(
        db: AsyncSession,
        order: Order,
        order_update: OrderUpdate,
    ) -> Order:
        """Update order."""
        if order_update.notes is not None:
            order.notes = order_update.notes
        if order_update.meta_data is not None:
            order.meta_data = order_update.meta_data
        
        await db.commit()
        # Reload with relationships
        return await OrderService.get_order(db, order.id)
    
    @staticmethod
    async def transition_order_state(
        db: AsyncSession,
        order: Order,
        action: str,
    ) -> Order:
        """Transition order to a new state using state machine."""
        # Normalize action name (handle common mistakes)
        action = action.lower().strip()
        if action == "cancelled":
            action = "cancel"
        
        state_machine = OrderStateMachine(order)
        
        # Check if already in target state
        if action == "cancel" and order.status == OrderStatus.CANCELLED:
            raise ValueError("Order is already cancelled")
        if action == "confirm" and order.status == OrderStatus.CONFIRMED:
            raise ValueError("Order is already confirmed")
        if action == "deliver" and order.status == OrderStatus.DELIVERED:
            raise ValueError("Order is already delivered")
        
        if not state_machine.can_transition(action):
            available = state_machine.get_available_transitions()
            current_state = order.status.value if hasattr(order.status, 'value') else str(order.status)
            raise ValueError(
                f"Cannot perform action '{action}' from state '{current_state}'. "
                f"Available actions: {available if available else 'None (order is in final state)'}"
            )
        
        # Trigger state transition
        getattr(state_machine, action)()
        
        await db.commit()
        
        # Trigger invoice generation if order is shipped
        if action == "ship":
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Queuing invoice generation task for order {order.id} (order_number: {order.order_number})")
                from app.tasks.invoice_tasks import generate_order_invoice
                task_result = generate_order_invoice.delay(order.id)
                logger.info(f"Invoice generation task queued with ID: {task_result.id}")
            except Exception as e:
                # Log error but don't fail the order state transition
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to queue invoice generation task for order {order.id}: {str(e)}. "
                    f"Error type: {type(e).__name__}. Make sure Celery worker is running."
                )
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Reload with relationships
        return await OrderService.get_order(db, order.id)

