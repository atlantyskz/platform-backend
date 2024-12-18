import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base


assigned_assistant = sa.Table(
    'assigned_assistants',
    Base.metadata,
    sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id', ondelete="CASCADE"), primary_key=True),
    sa.Column('assistant_id', sa.Integer, sa.ForeignKey('assistants.id', ondelete="CASCADE"), primary_key=True),
    sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False)
)
