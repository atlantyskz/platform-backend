from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_interaction import UserInteraction


class UserInteractionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_interaction(self, chat_id: str, instance_id: int, message_type: str) -> UserInteraction:
        interaction = UserInteraction(
            chat_id=chat_id,
            instance_id=instance_id,
            message_type=message_type
        )
        self.session.add(interaction)
        await self.session.flush()
        return interaction

    async def get_not_answered_by_chat(self, chat_id: str, instance_id: int, message_type: str):
        stmt = (
            select(
                UserInteraction
            )
            .where(
                UserInteraction.chat_id == chat_id,
                UserInteraction.instance_id == instance_id
            )
            .where(
                UserInteraction.message_type == message_type
            )
            .where(
                UserInteraction.is_answered == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def mark_answered(self, interaction_id: int):
        stmt = (
            update(
                UserInteraction)
            .where(
                UserInteraction.id == interaction_id
            )
            .values(
                is_answered=True
            )
        )
        await self.session.execute(stmt)

    async def get_interaction_by_chat_id(self, chat_id: int, instance_id: int):
        stmt = (
            select(UserInteraction)
            .where(
                UserInteraction.chat_id == chat_id,
                UserInteraction.instance_id == instance_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_interaction(self, chat_id: str, instance_id: int, data: dict):
        stmt = (
            update(UserInteraction)
            .where(UserInteraction.chat_id == chat_id, UserInteraction.instance_id == instance_id)
            .values(data)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
