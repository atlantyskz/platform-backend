from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from src.core.databases import insert_assistants, session_manager,insert_roles
from src.models import Base


class StoreManager:
    def __init__(self,):
        self.postgres = session_manager

    async def connect(self):
        async with self.postgres.connect() as conn:
            # await conn.run_sync(Base.metadata.create_all)
            pass
        async with self.postgres.session() as session:
            await insert_roles(session)
            # await insert_assistants(session)


    async def disconnect(self):
        await self.postgres.close()

_store: StoreManager | None = None


def get_store() -> StoreManager:
    if not _store:
        raise Exception("StoreManager is not initialized")
    return _store


async def connect_to_store() -> StoreManager:
    global _store

    if not _store:
        _store = StoreManager()
        await _store.connect()

    return _store


async def disconnect_from_store() -> None:
    global _store

    if _store:
        await _store.disconnect()
        _store = None




@asynccontextmanager
async def store_lifespan() -> AsyncGenerator[StoreManager, None]:
    await connect_to_store()
    try:
        yield get_store()
    finally:
        await disconnect_from_store()


@asynccontextmanager
async def lifespan(*_: FastAPI) -> AsyncGenerator[None, None]:
    async with store_lifespan():
        yield