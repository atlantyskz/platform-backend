from typing import Generic, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Base



class BaseRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

        