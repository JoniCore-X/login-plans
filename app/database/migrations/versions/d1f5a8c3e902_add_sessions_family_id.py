"""add sessions family id

Revision ID: d1f5a8c3e902
Revises: c9d2e4f6a1b7
Create Date: 2026-09-05 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f5a8c3e902'
down_revision: Union[str, Sequence[str], None] = 'c9d2e4f6a1b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sessions',
        sa.Column('family_id', sa.Uuid(), nullable=True),
    )
    op.execute(
        "UPDATE sessions SET family_id = id WHERE family_id IS NULL"
    )
    op.alter_column('sessions', 'family_id', nullable=False)
    op.create_index(
        op.f('ix_sessions_family_id'),
        'sessions',
        ['family_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_sessions_family_id'),
        table_name='sessions',
    )
    op.drop_column('sessions', 'family_id')
