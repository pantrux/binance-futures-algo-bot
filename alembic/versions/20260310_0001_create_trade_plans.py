"""create trade plans table"""

from alembic import op
import sqlalchemy as sa

revision = '20260310_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'trade_plans',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('side', sa.String(length=8), nullable=False),
        sa.Column('timeframe', sa.String(length=16), nullable=False),
        sa.Column('market_regime', sa.String(length=32), nullable=False),
        sa.Column('technical_score', sa.Float(), nullable=False),
        sa.Column('fundamental_score', sa.Float(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('aggregate_score', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=False),
        sa.Column('take_profit', sa.Float(), nullable=False),
        sa.Column('capital_usdt', sa.Float(), nullable=False),
        sa.Column('applied_risk_pct', sa.Float(), nullable=False),
        sa.Column('max_position_notional', sa.Float(), nullable=False),
        sa.Column('thesis', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('outline_url', sa.String(length=512), nullable=True),
        sa.Column('is_testnet', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_trade_plans_symbol', 'trade_plans', ['symbol'])
    op.create_index('ix_trade_plans_timeframe', 'trade_plans', ['timeframe'])
    op.create_index('ix_trade_plans_market_regime', 'trade_plans', ['market_regime'])
    op.create_index('ix_trade_plans_aggregate_score', 'trade_plans', ['aggregate_score'])
    op.create_index('ix_trade_plans_status', 'trade_plans', ['status'])
    op.create_index('ix_trade_plans_created_at', 'trade_plans', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_trade_plans_created_at', table_name='trade_plans')
    op.drop_index('ix_trade_plans_status', table_name='trade_plans')
    op.drop_index('ix_trade_plans_aggregate_score', table_name='trade_plans')
    op.drop_index('ix_trade_plans_market_regime', table_name='trade_plans')
    op.drop_index('ix_trade_plans_timeframe', table_name='trade_plans')
    op.drop_index('ix_trade_plans_symbol', table_name='trade_plans')
    op.drop_table('trade_plans')
