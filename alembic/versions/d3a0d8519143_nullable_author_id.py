"""nullable author_id

Revision ID: d3a0d8519143
Revises: 419d2d74be8c
Create Date: 2025-11-16 16:57:03.083914

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3a0d8519143"
down_revision: Union[str, Sequence[str], None] = "419d2d74be8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# note: revision "f03420f9a920" has been edited to set the author_id to True by default.
def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
