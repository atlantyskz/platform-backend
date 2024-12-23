"""fix: assistant column

Revision ID: 3c5afe8f5d07
Revises: 3882e921502f
Create Date: 2024-12-23 16:43:52.795195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c5afe8f5d07'
down_revision: Union[str, None] = '3882e921502f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assistants', sa.Column('status', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('assistants','status')

