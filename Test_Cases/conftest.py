"""
Pytest configuration and fixtures for testing.
"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from decimal import Decimal

from app.database import Base, get_db, get_async_session_local
from app.main import app
from app.models.order import Order, OrderItem, OrderStatus
from app.models.return_model import Return, ReturnItem, ReturnStatus, ReturnReason
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.invoice import Invoice, InvoiceType
from app.config import settings


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///:memory:"

# Create test engines
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

test_async_engine = create_async_engine(
    TEST_DATABASE_URL_ASYNC,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create a test database session."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
async def async_db_session():
    """Create an async test database session."""
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSessionLocal() as session:
        yield session
    
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(async_db_session):
    """Create a test client."""
    async def override_get_db():
        try:
            yield async_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "customer_id": 1,
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
        "items": [
            {
                "product_id": 101,
                "product_name": "Test Product A",
                "product_sku": "SKU-001",
                "unit_price": 100.00,
                "quantity": 2
            },
            {
                "product_id": 102,
                "product_name": "Test Product B",
                "product_sku": "SKU-002",
                "unit_price": 50.00,
                "quantity": 1
            }
        ],
        "shipping_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
            "country": "USA"
        },
        "billing_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
            "country": "USA"
        },
        "notes": "Test order"
    }


@pytest.fixture
def sample_order(db_session, sample_order_data):
    """Create a sample order in the database."""
    order = Order(
        order_number="ORD-TEST-001",
        customer_id=sample_order_data["customer_id"],
        customer_email=sample_order_data["customer_email"],
        customer_name=sample_order_data["customer_name"],
        status=OrderStatus.PENDING,
        subtotal=Decimal("250.00"),
        tax=Decimal("25.00"),
        shipping_cost=Decimal("5.00"),
        total=Decimal("280.00"),
        currency="USD",
        shipping_address=sample_order_data["shipping_address"],
        billing_address=sample_order_data["billing_address"],
        notes=sample_order_data["notes"],
    )
    db_session.add(order)
    db_session.flush()
    
    # Add order items
    for item_data in sample_order_data["items"]:
        item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            product_sku=item_data["product_sku"],
            unit_price=Decimal(str(item_data["unit_price"])),
            quantity=item_data["quantity"],
            total_price=Decimal(str(item_data["unit_price"] * item_data["quantity"])),
        )
        db_session.add(item)
    
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def sample_return_data(sample_order):
    """Sample return data for testing."""
    return {
        "order_id": sample_order.id,
        "reason": ReturnReason.DEFECTIVE,
        "reason_description": "Product arrived damaged",
        "items": [
            {
                "order_item_id": sample_order.items[0].id,
                "product_id": 101,
                "product_name": "Test Product A",
                "product_sku": "SKU-001",
                "quantity": 1,
                "condition": "damaged",
                "condition_notes": "Box was crushed"
            }
        ],
        "return_address": {
            "street": "456 Return St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345"
        },
        "notes": "Test return"
    }


@pytest.fixture
def sample_return(db_session, sample_order):
    """Create a sample return in the database."""
    return_obj = Return(
        return_number="RET-TEST-001",
        order_id=sample_order.id,
        status=ReturnStatus.INITIATED,
        reason=ReturnReason.DEFECTIVE,
        refund_amount=Decimal("100.00"),
        currency="USD",
        notes="Test return",
    )
    db_session.add(return_obj)
    db_session.flush()
    
    # Add return item
    return_item = ReturnItem(
        return_id=return_obj.id,
        order_item_id=sample_order.items[0].id,
        product_id=101,
        product_name="Test Product A",
        product_sku="SKU-001",
        quantity=1,
        refund_amount=Decimal("100.00"),
    )
    db_session.add(return_item)
    
    db_session.commit()
    db_session.refresh(return_obj)
    return return_obj


@pytest.fixture
def sample_payment(db_session, sample_order):
    """Create a sample payment in the database."""
    payment = Payment(
        payment_number="PAY-TEST-001",
        order_id=sample_order.id,
        status=PaymentStatus.PENDING,
        method=PaymentMethod.CREDIT_CARD,
        amount=Decimal("280.00"),
        currency="USD",
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def sample_invoice(db_session, sample_order):
    """Create a sample invoice in the database."""
    invoice = Invoice(
        invoice_number="INV-TEST-001",
        invoice_type=InvoiceType.ORDER,
        order_id=sample_order.id,
        file_path="invoices/test_invoice.pdf",
        file_name="test_invoice.pdf",
        file_size=1024,
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice

