from typing import Any
from pydantic import EmailStr
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import joinedload,defer
from src.models.role import Role
from src.models.user import User
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

        
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email).options(joinedload(User.role))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_user_id(self, user_id:int) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                joinedload(User.role),
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().first()
    

    
    async def get_current_user(self, user_id: int):
        stmt = (
            select(User)
            .options(joinedload(User.role))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "role": user.role.name if user.role else None,
            }
        return None
        
    async def create_user(self, attributes: dict) -> User:
        stmt = insert(User).values(**attributes).returning(User)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def delete_user(self,user_id:int):
        stmt = delete(User).where(User.id == user_id)
        await self.session.execute(stmt)
    
    async def update_user(self,user_id:int,attributes:dict):
        stmt = update(User).values(**attributes).where(User.id == user_id).returning(User)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    