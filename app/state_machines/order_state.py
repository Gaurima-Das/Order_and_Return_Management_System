from transitions import Machine
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.order import Order, OrderStatus


class OrderStateMachine:
    """
    State machine for managing order state transitions.
    
    States:
    - pending: Order created but not confirmed
    - confirmed: Order confirmed and payment processed
    - processing: Order being prepared for shipment
    - shipped: Order shipped to customer
    - delivered: Order delivered to customer
    - cancelled: Order cancelled
    - returned: Order returned by customer
    """
    
    def __init__(self, order: Order):
        self.order = order
        # Get current state as string value
        current_state = order.status.value if order.status else OrderStatus.PENDING.value
        
        self.machine = Machine(
            model=self,
            states=[
                OrderStatus.PENDING.value,
                OrderStatus.CONFIRMED.value,
                OrderStatus.PROCESSING.value,
                OrderStatus.SHIPPED.value,
                OrderStatus.DELIVERED.value,
                OrderStatus.CANCELLED.value,
                OrderStatus.RETURNED.value,
            ],
            initial=current_state,
            transitions=[
                # From pending
                {
                    "trigger": "confirm",
                    "source": OrderStatus.PENDING.value,
                    "dest": OrderStatus.CONFIRMED.value,
                    "before": "_before_confirm",
                    "after": "_after_confirm",
                },
                {
                    "trigger": "cancel",
                    "source": OrderStatus.PENDING.value,
                    "dest": OrderStatus.CANCELLED.value,
                    "before": "_before_cancel",
                    "after": "_after_cancel",
                },
                # From confirmed
                {
                    "trigger": "start_processing",
                    "source": OrderStatus.CONFIRMED.value,
                    "dest": OrderStatus.PROCESSING.value,
                    "after": "_after_start_processing",
                },
                {
                    "trigger": "cancel",
                    "source": OrderStatus.CONFIRMED.value,
                    "dest": OrderStatus.CANCELLED.value,
                    "before": "_before_cancel",
                    "after": "_after_cancel",
                },
                # From processing
                {
                    "trigger": "ship",
                    "source": OrderStatus.PROCESSING.value,
                    "dest": OrderStatus.SHIPPED.value,
                    "after": "_after_ship",
                },
                {
                    "trigger": "cancel",
                    "source": OrderStatus.PROCESSING.value,
                    "dest": OrderStatus.CANCELLED.value,
                    "before": "_before_cancel",
                    "after": "_after_cancel",
                },
                # From shipped
                {
                    "trigger": "deliver",
                    "source": OrderStatus.SHIPPED.value,
                    "dest": OrderStatus.DELIVERED.value,
                    "after": "_after_deliver",
                },
                # From delivered
                {
                    "trigger": "return_order",
                    "source": OrderStatus.DELIVERED.value,
                    "dest": OrderStatus.RETURNED.value,
                    "after": "_after_return",
                },
            ],
            auto_transitions=False,
            ignore_invalid_triggers=True,
        )
    
    def _before_confirm(self):
        """Validate before confirming order."""
        # Add validation logic here
        pass
    
    def _after_confirm(self):
        """Actions after confirming order."""
        self.order.previous_status = self.order.status
        self.order.status = OrderStatus.CONFIRMED
        self.order.confirmed_at = datetime.utcnow()
    
    def _after_start_processing(self):
        """Actions after starting processing."""
        self.order.previous_status = self.order.status
        self.order.status = OrderStatus.PROCESSING
    
    def _after_ship(self):
        """Actions after shipping order."""
        self.order.previous_status = self.order.status
        self.order.status = OrderStatus.SHIPPED
        self.order.shipped_at = datetime.utcnow()
        # Trigger invoice generation (will be handled by service layer)
    
    def _after_deliver(self):
        """Actions after delivering order."""
        self.order.previous_status = self.order.status
        self.order.status = OrderStatus.DELIVERED
        self.order.delivered_at = datetime.utcnow()
    
    def _before_cancel(self):
        """Validate before cancelling order."""
        # Add validation logic here (e.g., check if already shipped)
        if self.order.status == OrderStatus.SHIPPED:
            raise ValueError("Cannot cancel order that has already been shipped")
        if self.order.status == OrderStatus.DELIVERED:
            raise ValueError("Cannot cancel order that has already been delivered")
    
    def _after_cancel(self):
        """Actions after cancelling order."""
        self.order.previous_status = self.order.status
        self.order.status = OrderStatus.CANCELLED
        self.order.cancelled_at = datetime.utcnow()
    
    def _after_return(self):
        """Actions after returning order."""
        self.order.previous_status = self.order.status
        self.order.status = OrderStatus.RETURNED
    
    def can_transition(self, trigger: str) -> bool:
        """Check if a transition is possible."""
        return self.machine.get_triggers(self.state).__contains__(trigger)
    
    def get_available_transitions(self) -> list:
        """Get list of available transitions from current state."""
        return self.machine.get_triggers(self.state)
    
    def get_state(self) -> OrderStatus:
        """Get current state."""
        return OrderStatus(self.state)

