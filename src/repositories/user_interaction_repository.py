from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_interaction import UserInteraction


class UserInteractionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_interaction(self, data) -> UserInteraction:
        stmt = (
            insert(
                UserInteraction
            )
            .values(
                **data
            )
            .returning(
                UserInteraction
            )
        )
        interaction = await self.session.execute(stmt)
        return interaction.scalars().first()

    async def get_not_answered_by_chat(
            self,
            chat_id: str,
            instance_id: int,
            message_type: str
    ):
        stmt = (
            select(
                UserInteraction
            )
            .where(
                UserInteraction.chat_id == chat_id,
                UserInteraction.instance_id == instance_id,
                UserInteraction.is_last == True
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

    async def mark_answered(
            self,
            interaction_id: int,
            chat_id: str,
            is_answered: bool
    ):
        stmt = (
            update(
                UserInteraction)
            .where(
                UserInteraction.id == interaction_id,
                UserInteraction.chat_id == chat_id,
                UserInteraction.is_last == True
            )
            .values(
                is_answered=is_answered
            )
        )
        await self.session.execute(stmt)

    async def get_interaction_by_chat_id(
            self,
            chat_id: str,
            instance_id: int,
    ):
        stmt = (
            select(UserInteraction)
            .where(
                UserInteraction.chat_id == chat_id,
                UserInteraction.instance_id == instance_id,
                UserInteraction.is_last == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_interaction(
            self,
            chat_id: str,
            instance_id: int,
            data: dict
    ):
        stmt = (
            update(UserInteraction)
            .where(UserInteraction.chat_id == chat_id, UserInteraction.instance_id == instance_id)
            .values(data)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_interaction_by_session_id(
            self,
            chat_id: str,
            session_id: str
    ):
        stmt = (
            select(UserInteraction)
            .where(
                UserInteraction.chat_id == chat_id,
                UserInteraction.session_id == session_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_ignored_interactions(
            self,
            session_id: str
    ):
        stmt = (
            select(UserInteraction)
            .where(
                UserInteraction.session_id == session_id,
                UserInteraction.is_ignored == True,
                UserInteraction.is_last == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
