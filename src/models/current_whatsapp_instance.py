import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class CurrentWhatsappInstance(Base):
    __tablename__ = "current_whatsapp_instance"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
    whatsapp_instance_id = sa.Column(sa.Integer, sa.ForeignKey("whatsapp_instances.id"), primary_key=True)

    user = orm.relationship("User", back_populates="current_whatsapp_instance", uselist=False)
