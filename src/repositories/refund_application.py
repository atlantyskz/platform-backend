from src.models.refund_application import RefundApplication
from typing import  List
from sqlalchemy import insert, select, update
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import subqueryload,selectinload,joinedload

class RefundApplicationRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attributes: dict) -> RefundApplication:
        stmt = insert(RefundApplication).values(**attributes).returning(RefundApplication)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_refunds_by_organization_id(self,organization_id:int,status:str|None,limit:int|None, offset: int| None)->List[RefundApplication]:
        stmt = select(RefundApplication).where(RefundApplication.organization_id == organization_id).options(
            joinedload(RefundApplication.transaction)
        ).order_by(RefundApplication.created_at.desc())
        if status:
            stmt = stmt.where(RefundApplication.status == status)
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_refund_application(self,id: int) -> RefundApplication:
        stmt = select(RefundApplication).where(RefundApplication.id == id).options(
            joinedload(RefundApplication.transaction)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all_refund_applications(self,)->List[RefundApplication]:
        stmt = select(RefundApplication).options(
            joinedload(RefundApplication.transaction)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_refund(self,refund_application_id,attributes:dict)-> RefundApplication:
        stmt = (
            update(RefundApplication)
            .where(RefundApplication.id == refund_application_id)
            .values(**attributes)
            .returning(RefundApplication)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()