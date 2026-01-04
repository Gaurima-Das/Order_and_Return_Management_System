"""
Unit tests for State Machines.
"""
import pytest
from datetime import datetime

from app.state_machines.order_state import OrderStateMachine
from app.state_machines.return_state import ReturnStateMachine
from app.models.order import Order, OrderStatus
from app.models.return_model import Return, ReturnStatus


def test_order_state_machine_initialization(sample_order):
    """Test order state machine initialization."""
    machine = OrderStateMachine(sample_order)
    assert machine.state == OrderStatus.PENDING.value


def test_order_state_machine_transitions(sample_order):
    """Test order state machine transitions."""
    machine = OrderStateMachine(sample_order)
    
    # Test valid transitions
    assert machine.can_transition("confirm")
    machine.confirm()
    assert machine.state == OrderStatus.CONFIRMED.value
    
    assert machine.can_transition("start_processing")
    machine.start_processing()
    assert machine.state == OrderStatus.PROCESSING.value
    
    assert machine.can_transition("ship")
    machine.ship()
    assert machine.state == OrderStatus.SHIPPED.value


def test_order_state_machine_invalid_transition(sample_order):
    """Test invalid state transition."""
    machine = OrderStateMachine(sample_order)
    
    # Cannot ship from pending
    assert not machine.can_transition("ship")
    
    with pytest.raises(AttributeError):
        machine.ship()


def test_return_state_machine_initialization(sample_return):
    """Test return state machine initialization."""
    machine = ReturnStateMachine(sample_return)
    assert machine.state == ReturnStatus.INITIATED.value


def test_return_state_machine_transitions(sample_return):
    """Test return state machine transitions."""
    machine = ReturnStateMachine(sample_return)
    
    # Test valid transitions
    assert machine.can_transition("approve")
    machine.approve()
    assert machine.state == ReturnStatus.APPROVED.value
    
    assert machine.can_transition("schedule_pickup")
    machine.schedule_pickup()
    assert machine.state == ReturnStatus.PICKUP_SCHEDULED.value
    
    assert machine.can_transition("start_transit")
    machine.start_transit()
    assert machine.state == ReturnStatus.IN_TRANSIT.value
    
    assert machine.can_transition("receive")
    machine.receive()
    assert machine.state == ReturnStatus.RECEIVED.value
    
    assert machine.can_transition("process")
    machine.process()
    assert machine.state == ReturnStatus.PROCESSED.value


def test_return_state_machine_invalid_transition(sample_return):
    """Test invalid state transition."""
    machine = ReturnStateMachine(sample_return)
    
    # Cannot process from initiated
    assert not machine.can_transition("process")
    
    with pytest.raises(AttributeError):
        machine.process()


def test_get_available_transitions(sample_order):
    """Test getting available transitions."""
    machine = OrderStateMachine(sample_order)
    transitions = machine.get_available_transitions()
    
    assert "confirm" in transitions
    assert "cancel" in transitions
    assert "ship" not in transitions  # Cannot ship from pending

