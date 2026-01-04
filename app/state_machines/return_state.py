from transitions import Machine
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.return_model import Return, ReturnStatus


class ReturnStateMachine:
    """
    State machine for managing return state transitions.
    
    States:
    - initiated: Return request created
    - approved: Return approved by admin
    - rejected: Return rejected
    - pickup_scheduled: Pickup scheduled for return
    - in_transit: Return item in transit
    - received: Return item received at warehouse
    - processed: Return processed and verified
    - refunded: Refund processed
    - cancelled: Return cancelled
    """
    
    def __init__(self, return_obj: Return):
        self.return_obj = return_obj
        # Get current state as string value
        current_state = return_obj.status.value if return_obj.status else ReturnStatus.INITIATED.value
        
        self.machine = Machine(
            model=self,
            states=[
                ReturnStatus.INITIATED.value,
                ReturnStatus.APPROVED.value,
                ReturnStatus.REJECTED.value,
                ReturnStatus.PICKUP_SCHEDULED.value,
                ReturnStatus.IN_TRANSIT.value,
                ReturnStatus.RECEIVED.value,
                ReturnStatus.PROCESSED.value,
                ReturnStatus.REFUNDED.value,
                ReturnStatus.CANCELLED.value,
            ],
            initial=current_state,
            transitions=[
                # From initiated
                {
                    "trigger": "approve",
                    "source": ReturnStatus.INITIATED.value,
                    "dest": ReturnStatus.APPROVED.value,
                    "after": "_after_approve",
                },
                {
                    "trigger": "reject",
                    "source": ReturnStatus.INITIATED.value,
                    "dest": ReturnStatus.REJECTED.value,
                    "after": "_after_reject",
                },
                {
                    "trigger": "cancel",
                    "source": ReturnStatus.INITIATED.value,
                    "dest": ReturnStatus.CANCELLED.value,
                    "after": "_after_cancel",
                },
                # From approved
                {
                    "trigger": "schedule_pickup",
                    "source": ReturnStatus.APPROVED.value,
                    "dest": ReturnStatus.PICKUP_SCHEDULED.value,
                    "after": "_after_schedule_pickup",
                },
                {
                    "trigger": "reject",
                    "source": ReturnStatus.APPROVED.value,
                    "dest": ReturnStatus.REJECTED.value,
                    "after": "_after_reject",
                },
                {
                    "trigger": "cancel",
                    "source": ReturnStatus.APPROVED.value,
                    "dest": ReturnStatus.CANCELLED.value,
                    "after": "_after_cancel",
                },
                # From pickup_scheduled
                {
                    "trigger": "start_transit",
                    "source": ReturnStatus.PICKUP_SCHEDULED.value,
                    "dest": ReturnStatus.IN_TRANSIT.value,
                    "after": "_after_start_transit",
                },
                # From in_transit
                {
                    "trigger": "receive",
                    "source": ReturnStatus.IN_TRANSIT.value,
                    "dest": ReturnStatus.RECEIVED.value,
                    "after": "_after_receive",
                },
                # From received
                {
                    "trigger": "process",
                    "source": ReturnStatus.RECEIVED.value,
                    "dest": ReturnStatus.PROCESSED.value,
                    "after": "_after_process",
                },
                # From processed
                {
                    "trigger": "refund",
                    "source": ReturnStatus.PROCESSED.value,
                    "dest": ReturnStatus.REFUNDED.value,
                    "after": "_after_refund",
                },
            ],
            auto_transitions=False,
            ignore_invalid_triggers=True,
        )
    
    def _after_approve(self):
        """Actions after approving return."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.APPROVED
        self.return_obj.approved_at = datetime.utcnow()
    
    def _after_reject(self, reason: Optional[str] = None):
        """Actions after rejecting return."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.REJECTED
        if reason:
            self.return_obj.rejection_reason = reason
    
    def _after_schedule_pickup(self):
        """Actions after scheduling pickup."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.PICKUP_SCHEDULED
        self.return_obj.pickup_scheduled_at = datetime.utcnow()
    
    def _after_start_transit(self):
        """Actions after starting transit."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.IN_TRANSIT
    
    def _after_receive(self):
        """Actions after receiving return."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.RECEIVED
        self.return_obj.received_at = datetime.utcnow()
    
    def _after_process(self):
        """Actions after processing return."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.PROCESSED
        self.return_obj.processed_at = datetime.utcnow()
    
    def _after_refund(self):
        """Actions after refunding."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.REFUNDED
        self.return_obj.refunded_at = datetime.utcnow()
    
    def _after_cancel(self):
        """Actions after cancelling return."""
        self.return_obj.previous_status = self.return_obj.status
        self.return_obj.status = ReturnStatus.CANCELLED
    
    def can_transition(self, trigger: str) -> bool:
        """Check if a transition is possible."""
        return self.machine.get_triggers(self.state).__contains__(trigger)
    
    def get_available_transitions(self) -> list:
        """Get list of available transitions from current state."""
        return self.machine.get_triggers(self.state)
    
    def get_state(self) -> ReturnStatus:
        """Get current state."""
        return ReturnStatus(self.state)

