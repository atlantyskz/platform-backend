from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


class CurrentWhatsappInstanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_current_instance(self, user_id: int, whatsapp_instance_id: int):
        await self.session.execute(
            delete(models.CurrentWhatsappInstance
                   )
            .where(
                models.CurrentWhatsappInstance.user_id == user_id
            )
        )
        instance = models.CurrentWhatsappInstance(
            user_id=user_id,
            whatsapp_instance_id=whatsapp_instance_id
        )
        self.session.add(instance)

    async def get_current_instance_id(self, user_id: int) -> int | None:
        result = await self.session.execute(
            select(
                models.CurrentWhatsappInstance.whatsapp_instance_id)
            .where(
                models.CurrentWhatsappInstance.user_id == user_id
            )
        )
        return result.scalar()

    async def remove_current_instance(self, user_id: int):
        await self.session.execute(
            delete(
                models.CurrentWhatsappInstance)
            .where(
                models.CurrentWhatsappInstance.user_id == user_id
            )
        )
