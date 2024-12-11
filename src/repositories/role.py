from typing import Any
from pydantic import EmailStr
from sqlalchemy import insert, select
from src.models.user import User
from src.models.role import Role,RoleEnum
from src.repositories import BaseRepository

from sqlalchemy.ext.asyncio import AsyncSession

class RoleRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_role_by_name(self,role_name:RoleEnum)->Role:
        stmt = select(Role).where(Role.name == role_name.value)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_user_role(self, user_id: int)->Role:
        stmt = (
            select(Role)
            .join(User, User.role_id == Role.id)
            .filter(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar()  