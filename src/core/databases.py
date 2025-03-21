from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy import select
from src.models.assistant import Assistant,AssistantEnum
from src.models.role import Role, RoleEnum
from src.core.settings import settings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base


class DatabaseSessionManager:
    def __init__(self, url: str, engine_kwargs: dict[str, Any] = None):
        if engine_kwargs is None:
            engine_kwargs = {}

        self._engine = create_async_engine(url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncSession]:
        if not self._engine:
            raise Exception("DatabaseSessionManager is not initialized")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception as ex:
                await connection.rollback()
                raise ex

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if not self._sessionmaker:
            raise Exception("Session maker is not initialized")

        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception as ex:
                raise ex


session_manager =  DatabaseSessionManager(
    settings.get_db_url,
    {
    "echo": False,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,  
    "pool_pre_ping": True, 
})

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.settings import settings

engine = create_async_engine(
    settings.get_db_url,
    echo=False,
)


async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db():
    async with async_session_factory() as session:
        yield session
async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_manager.session() as session:
        yield session


async def insert_roles(session: AsyncSession):
    roles = await session.execute(select(Role.name))
    existing_roles = [role[0] for role in roles.fetchall()]
    for role in RoleEnum:
        if role.value not in existing_roles:
            new_role = Role(name=role.value)
            session.add(new_role)
    
    await session.commit()

async def insert_assistants(session:AsyncSession):
    assistants = await session.execute(select(Assistant.name))
    existing_assistants = [assistant[0] for assistant in assistants.fetchall()]
    for assistant in AssistantEnum:
        if assistant.display_name not in existing_assistants:
            new_assistant = Assistant(
                name=assistant.display_name,
                description=assistant.description,
                status = assistant.status,
                type=assistant.type
            )
            session.add(new_assistant)

    await session.commit()