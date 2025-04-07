import random
import string

from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories
from src.core import exceptions
from src.services.telegram_cli import TelegramCli


def generate_promo_code():
    strings = string.ascii_uppercase + string.digits
    return ''.join(random.choice(strings) for _ in range(10))


class PromoCodeController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.promo_code_repository = repositories.PromoCodeRepository(session)
        self.cash_balance_repository = repositories.CashBalanceRepository(session)
        self.organization_subscription_repository = repositories.OrganizationSubscriptionRepository(session)

    async def generate_promo_code(self, user_id: int, data: dict):
        db_promo_code = await self.promo_code_repository.get_user_promo_code(user_id)
        if db_promo_code is not None:
            raise exceptions.BadRequestException("Promo code already exists")

        generated_promo_code = generate_promo_code()
        while await self.promo_code_repository.get_promo_code(generated_promo_code) is not None:
            generated_promo_code = generate_promo_code()

        async with self.session:
            await self.promo_code_repository.create_promo_code(
                {
                    "user_id": user_id,
                    "promo_code": generated_promo_code,
                    **data,
                }
            )

            cash_balance = await self.cash_balance_repository.cash_balance(user_id)
            if cash_balance is None:
                await self.cash_balance_repository.create_cash_balance(
                    {
                        "user_id": user_id,
                        "balance": 0
                    }
                )

            await self.session.commit()

        name = data.get("name", "Неизвестно")
        phone = data.get("phone_number", "Неизвестно")
        email = data.get("email", "Неизвестно")
        message = f"\n📬 *Новая заявка от пользователя:*\n👤 Юзер Id: {user_id}\n👤 Имя: {name}\n📞 Телефон: {phone}\n📧 Почта: {email}"

        await TelegramCli().send_message(message, "feature")

        return {
            "promo_code": generated_promo_code,
            "detail": "Successfully created promo code"
        }

    async def get_user_promo_code(self, user_id: int):
        promo_code = await self.promo_code_repository.get_user_promo_code(user_id)
        if promo_code is None:
            raise exceptions.BadRequestException("Promo code does not exist")
        return promo_code

    async def update_promo_code(self, user_id: int, data: dict):
        promo_code = await self.promo_code_repository.get_user_promo_code(user_id)
        if promo_code is None:
            raise exceptions.BadRequestException("Promo code does not exist")
        async with self.session:
            await self.promo_code_repository.update_promo_code(promo_code.id, data)
            await self.session.commit()
        return {"detail": "Successfully updated promo code detail"}

    async def analyze_promo_code(self, user_id: int):
        user_cache_balance = await self.cash_balance_repository.cash_balance(user_id)
        if not user_cache_balance:
            return {"error": "No cache balance found"}

        analyze = await self.organization_subscription_repository.analyze_subscription(user_id)
        return {
            "balance": user_cache_balance.balance,
            "analyze": analyze
        }

    async def check_promo_code(self, promo_code: str):
        promo_code = await self.promo_code_repository.get_promo_code(promo_code)
        if promo_code is None:
            raise exceptions.BadRequestException("Promo code does not exist")
        return promo_code
