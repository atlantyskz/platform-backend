"""created interview questions

Revision ID: f3303784389f
Revises: cbf7cc7a81c0
Create Date: 2025-03-19 13:35:33.613420

"""
import enum
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3303784389f'
down_revision: Union[str, None] = 'cbf7cc7a81c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class CallStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IS_CALLED = "is_called"
    IN_PROGRESS = "in_progress"
    BUSY = "busy"


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('interview_common_questions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assistant_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )
    op.create_table('interview_individual_questions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('resume_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['resume_id'], ['favorite_resumes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['assistant_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )
    op.drop_index('ix_ai_clones_id', table_name='ai_clones')
    op.drop_table('ai_clones')
    op.execute("""
        CREATE TYPE callstatus AS ENUM ('not_started', 'is_called', 'in_progress', 'busy');
    """)

    op.add_column('favorite_resumes', sa.Column('call_status', sa.Enum(CallStatus, name='callstatus'), nullable=True))

    op.drop_column('favorite_resumes', 'is_called')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('favorite_resumes', sa.Column('is_called', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('favorite_resumes', 'call_status')
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
    op.drop_table('interview_individual_questions')
    op.drop_table('interview_common_questions')
    # ### end Alembic commands ###
