"""fix ChatMessageHistory

Revision ID: c0c8d596ea8f
Revises: 22a8884a9c31
Create Date: 2025-01-21 09:57:31.592822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0c8d596ea8f'
down_revision: Union[str, None] = '22a8884a9c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - adjusted ###
    op.execute("""
        ALTER TABLE chat_history_messages 
        ALTER COLUMN message 
        TYPE JSON 
        USING message::json;
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - adjusted ###
    op.execute("""
        ALTER TABLE chat_history_messages 
        ALTER COLUMN message 
        TYPE VARCHAR 
        USING message::text;
    """)
    # ### end Alembic commands ###