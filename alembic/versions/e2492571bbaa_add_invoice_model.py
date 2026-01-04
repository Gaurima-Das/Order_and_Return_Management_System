"""add_invoice_model

Revision ID: e2492571bbaa
Revises: 001_initial
Create Date: 2026-01-04 17:23:26.569837

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2492571bbaa'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    # Use String for Enum in SQLite, Enum for PostgreSQL
    invoice_type_col = sa.String(20) if is_sqlite else sa.Enum('ORDER', 'RETURN', name='invoicetype')
    
    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('invoice_type', invoice_type_col, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('return_id', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['return_id'], ['returns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_invoices_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_invoices_invoice_number'), ['invoice_number'], unique=True)
        batch_op.create_index(batch_op.f('ix_invoices_invoice_type'), ['invoice_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_invoices_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_invoices_return_id'), ['return_id'], unique=False)


def downgrade() -> None:
    # Drop indexes and table
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_invoices_return_id'))
        batch_op.drop_index(batch_op.f('ix_invoices_order_id'))
        batch_op.drop_index(batch_op.f('ix_invoices_invoice_type'))
        batch_op.drop_index(batch_op.f('ix_invoices_invoice_number'))
        batch_op.drop_index(batch_op.f('ix_invoices_id'))

    op.drop_table('invoices')
