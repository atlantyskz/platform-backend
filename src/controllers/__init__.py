from typing import TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories import BaseRepository

T = TypeVar('T', bound=BaseRepository)

class BaseController:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def repository(self, repo_type: Type[T]) -> T:
        return repo_type(self.session)