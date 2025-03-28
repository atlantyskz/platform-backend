"""AssistantSession add is_archived column

Revision ID: 7abe4732463c
Revises: 8af7331b12e6
Create Date: 2025-01-20 12:12:58.670339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7abe4732463c'
down_revision: Union[str, None] = '8af7331b12e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assistant_sessions', sa.Column('is_archived', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('assistant_sessions', 'is_archived')
    # ### end Alembic commands ###
