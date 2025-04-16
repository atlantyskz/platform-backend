from sqlalchemy import select, insert, update, delete

from src.models import CandidateInfo


class CandidateInfoRepository:
    def __init__(self, session):
        self.session = session

    async def get_candidate_info_by_id(self, candidate_id):
        stmt = select(CandidateInfo).where(CandidateInfo.id == candidate_id)
        candidate_info = await self.session.execute(stmt)
        return candidate_info.scalars().first()

    async def create_candidate_info(self, data: dict):
        stmt = insert(CandidateInfo).values(**data).returning(CandidateInfo)
        candidate_info = await self.session.execute(stmt)
        return candidate_info

    async def update_candidate_info(self, candidate_id, data):
        stmt = update(CandidateInfo).values(**data).where(CandidateInfo.id == candidate_id)
        candidate_info = await self.session.execute(stmt)
        return candidate_info

    async def delete_candidate_info(self, candidate_id):
        stmt = delete(CandidateInfo).where(CandidateInfo.id == candidate_id)
        candidate_info = await self.session.execute(stmt)
        return candidate_info.rowcount > 0

    async def list_candidate_info(self):
        stmt = select(CandidateInfo)
        candidate_info = await self.session.execute(stmt)
        return candidate_info.scalars().all()
