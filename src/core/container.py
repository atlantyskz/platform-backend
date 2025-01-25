from dependency_injector import containers
from dependency_injector import providers
from src.core.databases import async_session_factory


class Container(containers.Container):
    db = providers.Object(async_session_factory)
    