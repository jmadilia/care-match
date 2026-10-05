"""create comparison_cache table

Revision ID: a41c7e90b3d2
Revises: 9e683e6c7f9c
Create Date: 2026-10-05 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a41c7e90b3d2'
down_revision: Union[str, Sequence[str], None] = '9e683e6c7f9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('comparison_cache',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('clock_timestamp()'), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_index(op.f('ix_comparison_cache_created_at'), 'comparison_cache', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_comparison_cache_created_at'), table_name='comparison_cache')
    op.drop_table('comparison_cache')
