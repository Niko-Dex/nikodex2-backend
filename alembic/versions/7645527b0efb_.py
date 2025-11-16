"""empty message

Revision ID: 7645527b0efb
Revises: bb562358b75f
Create Date: 2025-11-16 13:10:46.395039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7645527b0efb'
down_revision: Union[str, Sequence[str], None] = 'bb562358b75f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
