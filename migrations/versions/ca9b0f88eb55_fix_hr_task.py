"""fix hr task

Revision ID: ca9b0f88eb55
Revises: 74c1f5d7f2af
Create Date: 2025-03-05 09:13:34.914824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ca9b0f88eb55'
down_revision: Union[str, None] = '74c1f5d7f2af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hr_assistant_tasks', sa.Column('vacancy_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('hr_assistant_tasks', 'vacancy_id')
    # ### end Alembic commands ###
