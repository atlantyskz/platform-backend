from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.discount import Discount
from src.models.user import User
from src.models.billing_transactions import BillingTransaction

class DiscountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_discount(self, value)->Discount:
        stmt = select(Discount).where(Discount.value == value)
        result = await self.session.execute(stmt)
        return result.scalars().first()