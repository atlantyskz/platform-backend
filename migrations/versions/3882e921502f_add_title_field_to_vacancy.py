"""add title field to Vacancy

Revision ID: 3882e921502f
Revises: 275cd81b04fe
Create Date: 2024-12-22 14:26:18.580165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3882e921502f'
down_revision: Union[str, None] = '275cd81b04fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vacancy', sa.Column('title', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vacancy', 'title')
    # ### end Alembic commands ###