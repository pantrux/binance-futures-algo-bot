"""add market data tables"""

from alembic import op
import sqlalchemy as sa

revision = '20260310_0003'
down_revision = '20260310_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'market_candles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('timeframe', sa.String(length=16), nullable=False),
        sa.Column('open_time_ms', sa.Integer(), nullable=False),
        sa.Column('close_time_ms', sa.Integer(), nullable=False),
        sa.Column('open_price', sa.Float(), nullable=False),
        sa.Column('high_price', sa.Float(), nullable=False),
        sa.Column('low_price', sa.Float(), nullable=False),
        sa.Column('close_price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('quote_volume', sa.Float(), nullable=False),
        sa.Column('trades_count', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=24), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_market_candles_symbol', 'market_candles', ['symbol'])
    op.create_index('ix_market_candles_timeframe', 'market_candles', ['timeframe'])
    op.create_index('ix_market_candles_open_time_ms', 'market_candles', ['open_time_ms'])
    op.create_index('ix_market_candles_created_at', 'market_candles', ['created_at'])

    op.create_table(
        'market_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(length=32), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=False),
        sa.Column('mark_price', sa.Float(), nullable=False),
        sa.Column('index_price', sa.Float(), nullable=False),
        sa.Column('open_interest', sa.Float(), nullable=False, server_default='0'),
        sa.Column('funding_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('volume_24h', sa.Float(), nullable=False, server_default='0'),
        sa.Column('source', sa.String(length=24), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_market_snapshots_symbol', 'market_snapshots', ['symbol'])
    op.create_index('ix_market_snapshots_captured_at', 'market_snapshots', ['captured_at'])


def downgrade() -> None:
    op.drop_index('ix_market_snapshots_captured_at', table_name='market_snapshots')
    op.drop_index('ix_market_snapshots_symbol', table_name='market_snapshots')
    op.drop_table('market_snapshots')
    op.drop_index('ix_market_candles_created_at', table_name='market_candles')
    op.drop_index('ix_market_candles_open_time_ms', table_name='market_candles')
    op.drop_index('ix_market_candles_timeframe', table_name='market_candles')
    op.drop_index('ix_market_candles_symbol', table_name='market_candles')
    op.drop_table('market_candles')
