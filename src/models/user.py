import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.permission import user_permissions

class User(Base,TimestampMixin):

    __tablename__ = 'users'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    firstname: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    lastname: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    email: so.Mapped[str] = so.mapped_column(sa.String,nullable=False,unique=True,index=True)
    password:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('roles.id'),nullable=False)
    is_verified: so.Mapped[bool] = so.mapped_column(sa.Boolean,default=False,nullable=True)
    
    members = so.relationship("OrganizationMember", back_populates="user",cascade="all, delete-orphan",passive_deletes=True) 
    role = so.relationship("Role",back_populates='users')
    
    permissions = so.relationship(
        'Permission', secondary=user_permissions, back_populates='users'
    )
    user_vacancies = so.relationship(
        "Vacancy",back_populates="user",cascade="all, delete-orphan"
    )
    favorite_resumes = so.relationship("FavoriteResume", back_populates="user", cascade="all, delete-orphan")
    user_feedbacks = so.relationship("UserFeedback", back_populates="user", )
    balance_usages = so.relationship('BalanceUsage', back_populates='user')
    billing_transactions = so.relationship('BillingTransaction', back_populates='user')
    refund_applications = so.relationship('RefundApplication', back_populates='user')
    hh_account = so.relationship("HHAccount", back_populates="user", uselist=False)

    def __str__(self):
        return f"{self.id}"