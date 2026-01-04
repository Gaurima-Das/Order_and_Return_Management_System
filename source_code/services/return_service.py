from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.return_model import Return, ReturnItem, ReturnStatus
from app.models.order import Order, OrderItem
from app.schemas.return_schema import ReturnCreate, ReturnUpdate
from app.state_machines.return_state import ReturnStateMachine


class ReturnService:
    """Service for return business logic."""
    
    @staticmethod
    def generate_return_number() -> str:
        """Generate unique return number."""
        return f"RET-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    async def create_return(db: AsyncSession, return_data: ReturnCreate) -> Return:
        """Create a new return request."""
        # Verify order exists and is eligible for return
        order_result = await db.execute(
            select(Order).where(Order.id == return_data.order_id)
        )
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"Order {return_data.order_id} not found")
        
        if order.status.value not in ["delivered", "returned"]:
            raise ValueError(f"Order {return_data.order_id} is not eligible for return")
        
        # Calculate refund amount from order items
        refund_amount = Decimal("0.00")
        return_items = []
        
        for item_data in return_data.items:
            # Get original order item
            order_item_result = await db.execute(
                select(OrderItem).where(OrderItem.id == item_data.order_item_id)
            )
            order_item = order_item_result.scalar_one_or_none()
            
            if not order_item:
                raise ValueError(f"Order item {item_data.order_item_id} not found")
            
            if order_item.order_id != order.id:
                raise ValueError(f"Order item {item_data.order_item_id} does not belong to order {return_data.order_id}")
            
            # Calculate refund for this item
            item_refund = order_item.unit_price * item_data.quantity
            refund_amount += item_refund
            
            return_items.append({
                "order_item_id": item_data.order_item_id,
                "product_id": item_data.product_id,
                "product_name": item_data.product_name,
                "product_sku": item_data.product_sku,
                "quantity": item_data.quantity,
                "refund_amount": item_refund,
                "condition": item_data.condition,
                "condition_notes": item_data.condition_notes,
            })
        
        # Create return
        return_obj = Return(
            return_number=ReturnService.generate_return_number(),
            order_id=return_data.order_id,
            status=ReturnStatus.INITIATED,
            reason=return_data.reason,
            reason_description=return_data.reason_description,
            refund_amount=refund_amount,
            currency=order.currency,
            return_address=return_data.return_address,
            notes=return_data.notes,
            meta_data=return_data.meta_data,
        )
        
        db.add(return_obj)
        await db.flush()  # Get return ID
        
        # Create return items
        for item_data in return_items:
            return_item = ReturnItem(
                return_id=return_obj.id,
                order_item_id=item_data["order_item_id"],
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                product_sku=item_data["product_sku"],
                quantity=item_data["quantity"],
                refund_amount=item_data["refund_amount"],
                condition=item_data["condition"],
                condition_notes=item_data["condition_notes"],
            )
            db.add(return_item)
        
        await db.commit()
        # Reload with relationships
        return await ReturnService.get_return(db, return_obj.id)
    
    @staticmethod
    async def get_return(db: AsyncSession, return_id: int) -> Optional[Return]:
        """Get return by ID."""
        result = await db.execute(
            select(Return)
            .options(selectinload(Return.items))
            .where(Return.id == return_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_returns(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_id: Optional[int] = None,
        status: Optional[ReturnStatus] = None,
    ) -> List[Return]:
        """List returns with filters."""
        query = select(Return).options(selectinload(Return.items))
        
        if order_id:
            query = query.where(Return.order_id == order_id)
        if status:
            query = query.where(Return.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Return.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_return(
        db: AsyncSession,
        return_obj: Return,
        return_update: ReturnUpdate,
    ) -> Return:
        """Update return."""
        if return_update.notes is not None:
            return_obj.notes = return_update.notes
        if return_update.tracking_number is not None:
            return_obj.tracking_number = return_update.tracking_number
        if return_update.meta_data is not None:
            return_obj.meta_data = return_update.meta_data
        
        await db.commit()
        # Reload with relationships
        return await ReturnService.get_return(db, return_obj.id)
    
    @staticmethod
    async def transition_return_state(
        db: AsyncSession,
        return_obj: Return,
        action: str,
        reason: Optional[str] = None,
    ) -> Return:
        """Transition return to a new state using state machine."""
        # Normalize action name
        action = action.lower().strip()
        
        state_machine = ReturnStateMachine(return_obj)
        
        # Check if already in target state
        if action == "approve" and return_obj.status == ReturnStatus.APPROVED:
            raise ValueError("Return is already approved")
        if action == "refund" and return_obj.status == ReturnStatus.REFUNDED:
            raise ValueError("Return is already refunded")
        if action == "reject" and return_obj.status == ReturnStatus.REJECTED:
            raise ValueError("Return is already rejected")
        
        if not state_machine.can_transition(action):
            available = state_machine.get_available_transitions()
            current_state = return_obj.status.value if hasattr(return_obj.status, 'value') else str(return_obj.status)
            raise ValueError(
                f"Cannot perform action '{action}' from state '{current_state}'. "
                f"Available actions: {available if available else 'None (return is in final state)'}"
            )
        
        # Trigger state transition
        if action == "reject" and reason:
            state_machine.reject(reason=reason)
        else:
            getattr(state_machine, action)()
        
        await db.commit()
        
        # Trigger invoice generation if return is processed
        if action == "process":
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Queuing credit memo generation task for return {return_obj.id} (return_number: {return_obj.return_number})")
                from app.tasks.invoice_tasks import generate_return_invoice
                task_result = generate_return_invoice.delay(return_obj.id)
                logger.info(f"Credit memo generation task queued with ID: {task_result.id}")
            except Exception as e:
                # Log error but don't fail the return state transition
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to queue credit memo generation task for return {return_obj.id}: {str(e)}. "
                    f"Error type: {type(e).__name__}. Make sure Celery worker is running."
                )
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Reload with relationships
        return await ReturnService.get_return(db, return_obj.id)

