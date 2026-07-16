"""add unique constraint on doctor name

Revision ID: 55b82b3c8489
Revises: 30fbf3c87626
Create Date: 2026-07-15 12:02:53.364047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55b82b3c8489'
down_revision: Union[str, Sequence[str], None] = '30fbf3c87626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uq_doctors_name", "doctors", ["name"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_doctors_name", "doctors", type_="unique")
