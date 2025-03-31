import random
import string

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException
from src.core.telegram_cli import TelegramCli
from src.repositories.promocode import PromoCodeRepository
from src.repositories.user_cache_balance import UserCacheBalanceRepository
from src.repositories.user_subs import UserSubsRepository


def generate_promo_code():
    strings = string.ascii_uppercase + string.digits
    return ''.join(random.choice(strings) for _ in range(10))


class PromoCodeController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.promocode_repo = PromoCodeRepository(session)
        self.user_subs_repo = UserSubsRepository(session)
        self.user_cache_balance_repo = UserCacheBalanceRepository(session)

    async def generate_promocode(self, user_id: int, data: dict):
        db_promocode = await self.promocode_repo.get_user_promo_code(user_id)
        if db_promocode is not None:
            raise BadRequestException("Promocode already exists")

        generated_promocode = generate_promo_code()
        while await self.promocode_repo.get_promo_code(generated_promocode) is not None:
            generated_promocode = generate_promo_code()

        async with self.session:
            await self.promocode_repo.create_promo_code({
                "user_id": user_id,
                "promo_code": generated_promocode,
                **data,
            })

            cache_balance = await self.user_cache_balance_repo.get_cache_balance(user_id)
            if cache_balance is None:
                await self.user_cache_balance_repo.create_cache_balance({
                    "user_id": user_id,
                    "balance": 0
                })

            await self.session.commit()
        name = data.get("name", "Неизвестно")
        phone = data.get("phone_number", "Неизвестно")
        email = data.get("email", "Неизвестно")
        message = f"\n📬 *Новая заявка от пользователя:*\n👤 Юзер Id: {user_id}\n👤 Имя: {name}\n📞 Телефон: {phone}\n📧 Почта: {email}"

        await TelegramCli().send_message(message, "feature")

        return {
            "promo_code": generated_promocode,
            "detail": "Successfully created promo code"
        }

    async def get_user_promo_code(self, user_id: int):
        db_promocode = await self.promocode_repo.get_user_promo_code(user_id)
        if db_promocode is None:
            raise BadRequestException("Promo code does not exist")
        return db_promocode

    async def update_promocode(self, user_id: int, data: dict):
        db_promocode = await self.promocode_repo.get_user_promo_code(user_id)
        if db_promocode is None:
            raise BadRequestException("Promo code does not exist")
        async with self.session:
            await self.promocode_repo.update_promo_code(db_promocode.id, data)
            await self.session.commit()
        return {"detail": "Successfully updated promo code detail"}

    async def analyze_promocode(self, user_id: int):
        user_cache_balance = await self.user_cache_balance_repo.get_cache_balance(user_id)
        if not user_cache_balance:
            return {"error": "No cache balance found"}

        data = user_cache_balance.__dict__.copy()
        data['analyze'] = await self.user_subs_repo.analyze_subscription(user_id)
        return data

    async def check_promocode(self, promo_code: str):
        db_promocode = await self.promocode_repo.get_promo_code(promo_code)
        if db_promocode is None:
            raise BadRequestException("Promo code does not exist")
        return db_promocode
