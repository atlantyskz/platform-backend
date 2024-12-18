"""fix session and task table
Revision ID: ac62758a2e84
Revises: 2097b70479d1
Create Date: 2024-12-13 08:28:37.829705
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ac62758a2e84'
down_revision: Union[str, None] = '2097b70479d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create new UUID columns
    op.add_column('assistant_sessions', sa.Column('uuid_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('hr_assistant_tasks', sa.Column('new_session_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Generate UUIDs and update the new columns while maintaining relationships
    op.execute("""
        WITH updated_sessions AS (
            UPDATE assistant_sessions 
            SET uuid_id = gen_random_uuid() 
            RETURNING id, uuid_id
        )
        UPDATE hr_assistant_tasks 
        SET new_session_id = updated_sessions.uuid_id 
        FROM updated_sessions 
        WHERE hr_assistant_tasks.session_id = updated_sessions.id
    """)
    
    # Drop the foreign key constraint
    op.drop_constraint('hr_assistant_tasks_session_id_fkey', 'hr_assistant_tasks', type_='foreignkey')
    
    # Drop old index
    op.drop_index('ix_assistant_sessions_id', table_name='assistant_sessions')
    
    # Drop old columns and rename new ones
    op.drop_column('assistant_sessions', 'id')
    op.alter_column('assistant_sessions', 'uuid_id',
                    new_column_name='id',
                    nullable=False,
                    server_default=None)
    
    op.drop_column('hr_assistant_tasks', 'session_id')
    op.alter_column('hr_assistant_tasks', 'new_session_id',
                    new_column_name='session_id',
                    nullable=False,
                    server_default=None)
    
    # Add back primary key and foreign key constraints
    op.execute('ALTER TABLE assistant_sessions ADD PRIMARY KEY (id)')
    op.create_foreign_key(
        'hr_assistant_tasks_session_id_fkey',
        'hr_assistant_tasks', 'assistant_sessions',
        ['session_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add task_id column
    op.add_column('hr_assistant_tasks', sa.Column('task_id', sa.String(), nullable=False, server_default=''))
    op.alter_column('hr_assistant_tasks', 'task_id', server_default=None)

def downgrade() -> None:
    # Create temporary integer ID columns
    op.add_column('assistant_sessions', sa.Column('int_id', sa.Integer(), autoincrement=True, nullable=True))
    op.add_column('hr_assistant_tasks', sa.Column('old_session_id', sa.Integer(), nullable=True))
    
    # Generate sequential IDs while maintaining relationships
    op.execute("""
        WITH updated_sessions AS (
            UPDATE assistant_sessions 
            SET int_id = nextval('assistant_sessions_id_seq') 
            RETURNING id, int_id
        )
        UPDATE hr_assistant_tasks 
        SET old_session_id = updated_sessions.int_id 
        FROM updated_sessions 
        WHERE hr_assistant_tasks.session_id = updated_sessions.id
    """)
    
    # Drop the foreign key constraint
    op.drop_constraint('hr_assistant_tasks_session_id_fkey', 'hr_assistant_tasks', type_='foreignkey')
    
    # Drop task_id column
    op.drop_column('hr_assistant_tasks', 'task_id')
    
    # Drop UUID columns and rename integer columns
    op.drop_column('assistant_sessions', 'id')
    op.alter_column('assistant_sessions', 'int_id',
                    new_column_name='id',
                    nullable=False,
                    server_default=None)
    
    op.drop_column('hr_assistant_tasks', 'session_id')
    op.alter_column('hr_assistant_tasks', 'old_session_id',
                    new_column_name='session_id',
                    nullable=False,
                    server_default=None)
    
    # Recreate index and constraints
    op.create_index('ix_assistant_sessions_id', 'assistant_sessions', ['id'], unique=False)
    op.create_foreign_key(
        'hr_assistant_tasks_session_id_fkey',
        'hr_assistant_tasks', 'assistant_sessions',
        ['session_id'], ['id'],
        ondelete='CASCADE'
    )