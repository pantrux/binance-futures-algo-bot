"""add final gate columns to trade_plans"""

from alembic import op
import sqlalchemy as sa

revision = '20260313_0004'
down_revision = '20260310_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('trade_plans', sa.Column('final_gate_score', sa.Float(), nullable=True))
    op.add_column('trade_plans', sa.Column('final_gate_passed', sa.Boolean(), nullable=True))
    op.add_column('trade_plans', sa.Column('final_gate_reason', sa.String(length=256), nullable=True))
    op.add_column('trade_plans', sa.Column('final_gate_pre_rejected_by_engine', sa.Boolean(), nullable=True))
    op.add_column('trade_plans', sa.Column('triggered_breakers', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('trade_plans', 'triggered_breakers')
    op.drop_column('trade_plans', 'final_gate_pre_rejected_by_engine')
    op.drop_column('trade_plans', 'final_gate_reason')
    op.drop_column('trade_plans', 'final_gate_passed')
    op.drop_column('trade_plans', 'final_gate_score')
