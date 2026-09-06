"""add email verification columns to users

Revision ID: a1b2c3d4e5f6
Revises: f3a8c1d5e927
Create Date: 2026-09-05 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3a8c1d5e927'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'email_verified_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'verification_token_hash',
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'verification_token_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        'uq_users_verification_token_hash',
        'users',
        ['verification_token_hash'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'uq_users_verification_token_hash',
        'users',
        type_='unique',
    )
    op.drop_column('users', 'verification_token_expires_at')
    op.drop_column('users', 'verification_token_hash')
    op.drop_column('users', 'email_verified_at')
