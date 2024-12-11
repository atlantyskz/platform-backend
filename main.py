from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.routers.handle_files import handle_files_router
from src.routers.api.v1.auth import auth_router
from src.routers.api.v1.hr_agent import hr_agent_router
from src.routers.api.v1.organization import organization_router
from src.routers.api.v1.organization_member import organization_member_router
from fastapi.middleware.cors import CORSMiddleware
from src.core.store import lifespan

origins = [
    "http://localhost",  
    "http://localhost:3000",  
]


def create_app()->FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.include_router(handle_files_router)
    app.include_router(auth_router)
    app.include_router(hr_agent_router)
    app.include_router(organization_router)
    app.include_router(organization_member_router)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )    
    return app

app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=9000,
        reload=True
    )