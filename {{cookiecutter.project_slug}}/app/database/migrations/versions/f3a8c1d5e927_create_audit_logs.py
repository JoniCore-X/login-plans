"""create audit_logs table

Revision ID: f3a8c1d5e927
Revises: e2f7b9a4d316
Create Date: 2026-09-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f3a8c1d5e927'
down_revision: Union[str, Sequence[str], None] = 'e2f7b9a4d316'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'event_type',
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column(
            'payload',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            'occurred_at',
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_audit_logs_user_time',
        'audit_logs',
        ['user_id', sa.text('occurred_at DESC')],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        'ix_audit_logs_user_time',
        table_name='audit_logs',
    )
    op.drop_table('audit_logs')
