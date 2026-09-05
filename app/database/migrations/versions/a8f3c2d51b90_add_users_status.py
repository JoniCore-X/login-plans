"""add users status and timestamptz

Revision ID: a8f3c2d51b90
Revises: f794bc810470
Create Date: 2026-09-05 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8f3c2d51b90'
down_revision: Union[str, Sequence[str], None] = 'f794bc810470'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'status',
            sa.String(length=32),
            server_default='active',
            nullable=False,
        ),
    )
    op.alter_column(
        'users',
        'created_at',
        type_=sa.DateTime(timezone=True),
    )
    op.alter_column(
        'users',
        'updated_at',
        type_=sa.DateTime(timezone=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users',
        'updated_at',
        type_=sa.DateTime(),
    )
    op.alter_column(
        'users',
        'created_at',
        type_=sa.DateTime(),
    )
    op.drop_column('users', 'status')
