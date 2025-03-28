"""in billing added subscription id 

Revision ID: 1e194e91e69e
Revises: 3ce8200f6301
Create Date: 2025-03-28 17:16:37.237137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1e194e91e69e'
down_revision: Union[str, None] = '3ce8200f6301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_ai_clones_id', table_name='ai_clones')
    op.drop_table('ai_clones')
    op.alter_column('balances', 'subscription',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.add_column('billing_transactions', sa.Column('subscription_id', sa.Boolean(), nullable=True))
    op.alter_column('billing_transactions', 'atl_tokens',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('billing_transactions', 'atl_tokens',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('billing_transactions', 'subscription_id')
    op.alter_column('balances', 'subscription',
               existing_type=sa.BOOLEAN(),
               nullable=True)
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
