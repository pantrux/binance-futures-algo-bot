"""add orders positions risk events"""

from alembic import op
import sqlalchemy as sa

revision = '20260310_0002'
down_revision = '20260310_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('trade_plan_id', sa.Integer(), sa.ForeignKey('trade_plans.id'), nullable=False),
        sa.Column('venue', sa.String(length=32), nullable=False),
        sa.Column('external_order_id', sa.String(length=128), nullable=True),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('side', sa.String(length=8), nullable=False),
        sa.Column('order_type', sa.String(length=24), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('executed_quantity', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_testnet', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_orders_trade_plan_id', 'orders', ['trade_plan_id'])
    op.create_index('ix_orders_external_order_id', 'orders', ['external_order_id'])
    op.create_index('ix_orders_symbol', 'orders', ['symbol'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])

    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('trade_plan_id', sa.Integer(), sa.ForeignKey('trade_plans.id'), nullable=True),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('side', sa.String(length=8), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('mark_price', sa.Float(), nullable=False),
        sa.Column('unrealized_pnl', sa.Float(), nullable=False, server_default='0'),
        sa.Column('leverage', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('is_testnet', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_positions_trade_plan_id', 'positions', ['trade_plan_id'])
    op.create_index('ix_positions_symbol', 'positions', ['symbol'])
    op.create_index('ix_positions_status', 'positions', ['status'])
    op.create_index('ix_positions_opened_at', 'positions', ['opened_at'])

    op.create_table(
        'risk_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('trade_plan_id', sa.Integer(), sa.ForeignKey('trade_plans.id'), nullable=True),
        sa.Column('event_type', sa.String(length=48), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_risk_events_trade_plan_id', 'risk_events', ['trade_plan_id'])
    op.create_index('ix_risk_events_event_type', 'risk_events', ['event_type'])
    op.create_index('ix_risk_events_severity', 'risk_events', ['severity'])
    op.create_index('ix_risk_events_created_at', 'risk_events', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_risk_events_created_at', table_name='risk_events')
    op.drop_index('ix_risk_events_severity', table_name='risk_events')
    op.drop_index('ix_risk_events_event_type', table_name='risk_events')
    op.drop_index('ix_risk_events_trade_plan_id', table_name='risk_events')
    op.drop_table('risk_events')

    op.drop_index('ix_positions_opened_at', table_name='positions')
    op.drop_index('ix_positions_status', table_name='positions')
    op.drop_index('ix_positions_symbol', table_name='positions')
    op.drop_index('ix_positions_trade_plan_id', table_name='positions')
    op.drop_table('positions')

    op.drop_index('ix_orders_created_at', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_symbol', table_name='orders')
    op.drop_index('ix_orders_external_order_id', table_name='orders')
    op.drop_index('ix_orders_trade_plan_id', table_name='orders')
    op.drop_table('orders')
