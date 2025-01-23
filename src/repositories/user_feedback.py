from typing import Any
from pydantic import EmailStr
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import joinedload,defer
from src.models.user_feedback import UserFeedback
from src.models.role import Role, RoleEnum
from src.models.user import User
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

class UserFeedbackRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attributes:dict):
        
        user_feedback = UserFeedback(**attributes)
        self.session.add(user_feedback)
        await self.session.flush()
        return user_feedback