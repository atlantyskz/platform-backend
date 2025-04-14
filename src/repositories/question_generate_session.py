from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


class QuestionGenerateSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_session_id(self, session_id: str) -> Optional[models.QuestionGenerateSession]:
        result = await self.session.execute(
            select(models.QuestionGenerateSession).where(
                models.QuestionGenerateSession.session_id == session_id).order_by("created_at")
        )
        return result.scalars().first()

    async def create(self, session_id: str) -> models.QuestionGenerateSession:
        new_session = models.QuestionGenerateSession(
            session_id=session_id,
            status=models.GenerateStatus.PENDING,
        )
        self.session.add(new_session)
        await self.session.flush()
        return new_session

    async def update_status(
            self,
            session_id: str,
            status: models.GenerateStatus,
            error: Optional[str] = None
    ) -> None:
        stmt = (
            update(models.QuestionGenerateSession)
            .where(models.QuestionGenerateSession.session_id == session_id)
            .values(status=status, error=error)
        )
        await self.session.execute(stmt)

    async def delete(self, session_id: str):
        stmt = (
            delete(models.QuestionGenerateSession)
            .where(models.QuestionGenerateSession.session_id == session_id)
            .where(models.QuestionGenerateSession.status == models.GenerateStatus.FAILURE)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
