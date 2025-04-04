"""added phone number in user table

Revision ID: aa24c991fe05
Revises: e684026e9467
Create Date: 2025-03-20 13:33:45.461948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aa24c991fe05'
down_revision: Union[str, None] = 'e684026e9467'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    op.drop_column('users', 'phone_number')
    op.create_table('ai_clones',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('agreement_video_path', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('sample_video_path', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('gender', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('lipsynch_text', sa.VARCHAR(length=3000), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='ai_clones_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='ai_clones_pkey')
    )
    op.create_index('ix_ai_clones_id', 'ai_clones', ['id'], unique=False)
    # ### end Alembic commands ###
