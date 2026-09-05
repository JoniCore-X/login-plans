"""add sessions credential hash

Revision ID: c9d2e4f6a1b7
Revises: b4e7a91c2f03
Create Date: 2026-09-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d2e4f6a1b7'
down_revision: Union[str, Sequence[str], None] = 'b4e7a91c2f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sessions',
        sa.Column(
            'credential_hash',
            sa.String(length=64),
            nullable=False,
        ),
    )
    op.create_index(
        op.f('ix_sessions_credential_hash'),
        'sessions',
        ['credential_hash'],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_sessions_credential_hash'),
        table_name='sessions',
    )
    op.drop_column('sessions', 'credential_hash')
