import sqlalchemy as sa
import sqlalchemy.orm as so

from src.models import Base, TimestampMixin

user_instance_association = sa.Table(
    "user_instance_association",
    Base.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("whatsapp_instance_id", sa.ForeignKey("whatsapp_instances.id", ondelete="CASCADE"), primary_key=True),
)


class WhatsappInstance(Base, TimestampMixin):
    __tablename__ = 'whatsapp_instances'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    instance_name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    instance_id: so.Mapped[str] = so.mapped_column(sa.String)
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    is_primary: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    instance_type: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)  # 'shared' or 'personal'
    instance_token: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)

    organization_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id'), nullable=False)

    def __str__(self):
        return f"{self.instance_name} ({self.instance_type})"
