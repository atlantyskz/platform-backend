"""add FavoriteResume table

Revision ID: 5b8d9131b112
Revises: 4ba0bca15c65
Create Date: 2024-12-19 11:30:37.522666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b8d9131b112'
down_revision: Union[str, None] = '4ba0bca15c65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###