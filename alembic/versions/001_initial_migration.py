"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    # Use TEXT for JSON in SQLite, JSON for PostgreSQL
    json_type = sa.Text() if is_sqlite else postgresql.JSON(astext_type=sa.Text())
    # Use String for Enum in SQLite, Enum for PostgreSQL
    status_enum = sa.String(20) if is_sqlite else sa.Enum('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED', name='orderstatus')
    return_status_enum = sa.String(20) if is_sqlite else sa.Enum('INITIATED', 'APPROVED', 'REJECTED', 'PICKUP_SCHEDULED', 'IN_TRANSIT', 'RECEIVED', 'PROCESSED', 'REFUNDED', 'CANCELLED', name='returnstatus')
    return_reason_enum = sa.String(20) if is_sqlite else sa.Enum('DEFECTIVE', 'WRONG_ITEM', 'NOT_AS_DESCRIBED', 'DAMAGED', 'SIZE_ISSUE', 'CHANGE_OF_MIND', 'OTHER', name='returnreason')
    payment_status_enum = sa.String(20) if is_sqlite else sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED', 'CANCELLED', name='paymentstatus')
    payment_method_enum = sa.String(20) if is_sqlite else sa.Enum('CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'BANK_TRANSFER', 'STRIPE', 'OTHER', name='paymentmethod')
    
    # SQLite doesn't support functions in DEFAULT, use CURRENT_TIMESTAMP or None
    datetime_default = None if is_sqlite else sa.text('now()')
    # Create orders table
    orders_table = op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('status', status_enum, nullable=False),
        sa.Column('previous_status', status_enum, nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tax', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('shipping_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('shipping_address', json_type, nullable=False),
        sa.Column('billing_address', json_type, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('meta_data', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)

    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('product_sku', sa.String(length=100), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('meta_data', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_product_id'), 'order_items', ['product_id'], unique=False)

    # Create returns table
    op.create_table(
        'returns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('return_number', sa.String(length=50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', return_status_enum, nullable=False),
        sa.Column('previous_status', return_status_enum, nullable=True),
        sa.Column('reason', return_reason_enum, nullable=False),
        sa.Column('reason_description', sa.Text(), nullable=True),
        sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('refund_method', sa.String(length=50), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('return_address', json_type, nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('meta_data', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pickup_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_returns_id'), 'returns', ['id'], unique=False)
    op.create_index(op.f('ix_returns_return_number'), 'returns', ['return_number'], unique=True)
    op.create_index(op.f('ix_returns_order_id'), 'returns', ['order_id'], unique=False)
    op.create_index(op.f('ix_returns_status'), 'returns', ['status'], unique=False)

    # Create return_items table
    op.create_table(
        'return_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('return_id', sa.Integer(), nullable=False),
        sa.Column('order_item_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('product_sku', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.ForeignKeyConstraint(['return_id'], ['returns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_return_items_id'), 'return_items', ['id'], unique=False)
    op.create_index(op.f('ix_return_items_return_id'), 'return_items', ['return_id'], unique=False)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', payment_status_enum, nullable=False),
        sa.Column('method', payment_method_enum, nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('refunded_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('gateway_response', json_type, nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('meta_data', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_payment_number'), 'payments', ['payment_number'], unique=True)
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_transaction_id'), 'payments', ['transaction_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_transaction_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_payment_number'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_return_items_return_id'), table_name='return_items')
    op.drop_index(op.f('ix_return_items_id'), table_name='return_items')
    op.drop_table('return_items')
    op.drop_index(op.f('ix_returns_status'), table_name='returns')
    op.drop_index(op.f('ix_returns_order_id'), table_name='returns')
    op.drop_index(op.f('ix_returns_return_number'), table_name='returns')
    op.drop_index(op.f('ix_returns_id'), table_name='returns')
    op.drop_table('returns')
    op.drop_index(op.f('ix_order_items_product_id'), table_name='order_items')
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_index(op.f('ix_order_items_id'), table_name='order_items')
    op.drop_table('order_items')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_customer_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_number'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')

