"""add request_id to audit_logs

Revision ID: b4c5d6e7f8a9
Revises: a1b2c3d4e5f6
Create Date: 2026-09-06 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'audit_logs',
        sa.Column(
            'request_id',
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_audit_logs_request_id',
        'audit_logs',
        ['request_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        'ix_audit_logs_request_id',
        table_name='audit_logs',
    )
    op.drop_column('audit_logs', 'request_id')
