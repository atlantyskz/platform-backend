from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

from src import models


class InstanceTypeEnum(str, Enum):
    SHARED = "shared"
    PERSONAL = "personal"


@dataclass
class WhatsappInstanceDTO:
    instance_name: str
    instance_id: str
    is_primary: bool
    instance_type: InstanceTypeEnum
    organization_id: int
    instance_token: str


class WhatsappInstanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_whatsapp_instance(self, data: WhatsappInstanceDTO):
        stmt = (
            insert(models.WhatsappInstance)
            .values(**asdict(data))
            .returning(models.WhatsappInstance)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_instance(self, instance_name: str) -> bool:
        stmt = delete(models.WhatsappInstance).where(
            models.WhatsappInstance.instance_name == instance_name
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_all_by_organization(self, organization_id: int, is_primary: bool) -> list[models.WhatsappInstance]:
        stmt = (
            select(models.WhatsappInstance, models.user_instance_association, models.User.email, )
            .select_from(models.WhatsappInstance)
            .join(
                models.user_instance_association,
                models.user_instance_association.c.whatsapp_instance_id == models.WhatsappInstance.id
            )
            .join(
                models.User,
                models.User.id == models.user_instance_association.c.user_id
            )
            .where(
                models.WhatsappInstance.organization_id == organization_id,
                models.WhatsappInstance.is_primary == is_primary
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_organization_id(self, organization_id: int) -> models.WhatsappInstance:
        stmt = (
            select(models.WhatsappInstance)
            .where(
                and_(
                    models.WhatsappInstance.organization_id == organization_id,
                    models.WhatsappInstance.is_primary.is_(True)
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_instance_id(self, instance_id: str) -> models.WhatsappInstance:
        stmt = (
            select(models.WhatsappInstance)
            .where(models.WhatsappInstance.instance_id == instance_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
