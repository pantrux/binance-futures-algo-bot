"""add context_json to risk_events"""

from alembic import op
import sqlalchemy as sa

revision = '20260316_0005'
down_revision = '20260313_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'risk_events',
        sa.Column('context_json', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.alter_column('risk_events', 'context_json', server_default=None)


def downgrade() -> None:
    op.drop_column('risk_events', 'context_json')
