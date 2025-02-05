from typing import Optional
from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.models.billing_transactions import BillingTransaction

class BillingTransactionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_refunds_by_transaction(self, transaction_id: int):
        stmt = select(BillingTransaction).where(
            and_(
                BillingTransaction.id == transaction_id,
                BillingTransaction.status == 'refunded'
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, attributes: dict):
        stmt = insert(BillingTransaction).values(**attributes).returning(BillingTransaction)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def update(self, transaction_id, attributes: dict):
        stmt = (
            update(BillingTransaction)
            .where(BillingTransaction.id == transaction_id)
            .values(**attributes)
            .returning(BillingTransaction)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_invoice_id(self, invoice_id: str) -> BillingTransaction:
        stmt = select(BillingTransaction).where(BillingTransaction.invoice_id == invoice_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    async def get_all_by_user_id(self, user_id: int):
        stmt = select(BillingTransaction).where(BillingTransaction.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_by_organization_id(self, organization_id: int, status: Optional[str], limit: int = 10, offset: int = 0)->list[BillingTransaction]:
        stmt = (
            select(BillingTransaction)
            .join(User, BillingTransaction.user_id == User.id)
            .where(BillingTransaction.organization_id == organization_id)
            .order_by(BillingTransaction.created_at.desc())
        )
        
        if status is not None:
            stmt = stmt.where(BillingTransaction.status == status)
        
        # Добавляем пагинацию
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_transactions(self,user_id: Optional[int], organization_id: Optional[int], status: Optional[str]):
        stmt = select(BillingTransaction).filter(
            (user_id is None or BillingTransaction.user_id == user_id),
            (organization_id is None or BillingTransaction.organization_id == organization_id),
            (status is None or BillingTransaction.status == status)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_transaction(self, transaction_id: int,user_id: int, organization_id: int):
        stmt = select(BillingTransaction).where(
            and_(
                BillingTransaction.id == transaction_id,
                BillingTransaction.organization_id == organization_id,
                BillingTransaction.user_id == user_id,
                BillingTransaction.status == 'charged')
            )
        result = await self.session.execute(stmt)
        return result.scalars().first()