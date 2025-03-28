from sqlalchemy import update, select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PromoCode


class PromoCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_promo_code(self, user_id) -> PromoCode:
        stmt = select(PromoCode).where(PromoCode.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_promo_code(self, data: dict) -> PromoCode:
        stmt = insert(PromoCode).values(**data).returning(PromoCode)
        promo_code = await self.session.execute(stmt)
        return promo_code.scalar_one_or_none()

    async def update_promo_code(self, promo_code_id, data: dict) -> PromoCode:
        stmt = update(PromoCode).values(**data).where(PromoCode.id == promo_code_id).returning(PromoCode)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_promo_code(self, promo_code) -> PromoCode:
        stmt = select(PromoCode).where(PromoCode.promo_code == promo_code)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
