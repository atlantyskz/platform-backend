from dataclasses import dataclass, asdict
from typing import List

from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


@dataclass
class WhatsappInstanceAssociation:
    user_id: int
    whatsapp_instance_id: int


class WhatsappInstanceAssociationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sub_instance(self, data: WhatsappInstanceAssociation):
        stmt = insert(models.user_instance_association).values(
            **asdict(data)
        )
        sub_instance = await self.session.execute(stmt)
        return sub_instance

    async def delete_instance(self, user_id: int, organization_instance_id: int) -> bool:
        stmt = delete(models.user_instance_association).where(
            models.user_instance_association.c.user_id == user_id,
            models.user_instance_association.c.instance_id == organization_instance_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def user_whatsapp_instance(self, user_id: int, organization_id: int):
        stmt = (
            select(models.WhatsappInstance)
            .select_from(models.WhatsappInstance)
            .join(
                models.user_instance_association,
                models.user_instance_association.c.whatsapp_instance_id == models.WhatsappInstance.id
            )
            .where(
                models.user_instance_association.c.user_id == user_id,
                models.WhatsappInstance.organization_id == organization_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()