from sqlalchemy import delete, insert, select
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vacancy_requirement import VacancyRequirement
from src.models.assigned_assistant import assigned_assistant


class VacancyRequirementRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create(self,attributes: dict):
        stmt = VacancyRequirement(**attributes)
        self.session.add(stmt)
        return stmt
    
    async def get_by_session_id(self,session_id: str):
        stmt = select(VacancyRequirement).where(VacancyRequirement.session_id == session_id)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_text_by_hash(self, text_hash: str)->VacancyRequirement:
        requirement = await self.session.execute(
            select(VacancyRequirement.requirement_text)
            .where(VacancyRequirement.requirement_hash == text_hash)
        )
        return requirement.scalar_one_or_none()

