"""create plans table

Revision ID: e2f7b9a4d316
Revises: d1f5a8c3e902
Create Date: 2026-09-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f7b9a4d316'
down_revision: Union[str, Sequence[str], None] = 'd1f5a8c3e902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column(
            'description',
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_plans_user_id'),
        'plans',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_plans_status'),
        'plans',
        ['status'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_plans_status'), table_name='plans')
    op.drop_index(op.f('ix_plans_user_id'), table_name='plans')
    op.drop_table('plans')
