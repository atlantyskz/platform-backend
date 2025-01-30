from contextlib import asynccontextmanager
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Request,status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from src.routers.api.v1.auth import auth_router
from src.routers.api.v1.hr_agent import hr_agent_router
from src.routers.api.v1.organization import organization_router
from src.routers.api.v1.organization_member import organization_member_router
from src.routers.api.v1.assistant import assistant_router
from src.routers.api.v1.user_feedback import  user_feedback_router
from src.routers.api.v1.billing import billing_router
from src.routers.api.v1.balance import balance_router
from fastapi.middleware.cors import CORSMiddleware
from src.core.store import lifespan
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi


origins = [
    "http://localhost",  
    "http://localhost:3000",  
]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FastAPI Swagger",
        version="3.0.3",
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3"
    app.openapi_schema = openapi_schema 
    return app.openapi_schema

def register_static_docs_routers(app: FastAPI):
    @app.get("/api/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
                openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/api/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0-rc.55/bundles/redoc.standalone.js",
        )

    @app.get("/api/openapi.json", include_in_schema=False)
    async def get_openapi_json():
        schema = app.openapi()
        print(f"OpenAPI schema requested. Schema size: {len(str(schema))} characters")
        return JSONResponse(content=schema)


def create_app(create_custom_static_urls: bool = False) -> FastAPI:
    app = FastAPI(
            title="Platform Backend",
            lifespan=lifespan,
            docs_url=None if create_custom_static_urls else '/api/docs',
            redoc_url=None if create_custom_static_urls else '/api/redoc',
            openapi_url="/api/openapi.json"  
    )
    app.include_router(auth_router)
    app.include_router(hr_agent_router)
    app.include_router(organization_router)
    app.include_router(organization_member_router)
    app.include_router(assistant_router)
    app.include_router(user_feedback_router)
    app.include_router(billing_router)
    app.include_router(balance_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )    
    if create_custom_static_urls:
        register_static_docs_routers(app)
    else:
        @app.get("/api/openapi.json", include_in_schema=False)
        async def get_openapi_json():
            schema = app.openapi()
            return JSONResponse(content=schema)
    app.openapi = custom_openapi
    return app

app = create_app(create_custom_static_urls=True)


from sqlalchemy.exc import IntegrityError,DBAPIError,SQLAlchemyError



# Глобальный обработчик IntegrityError
@app.exception_handler(IntegrityError)
async def database_error_handler(request, exc: IntegrityError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database Error", "detail": str(exc.orig)},
    )

@app.exception_handler(DBAPIError)
async def database_error_handler(request, exc: DBAPIError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database Error", "detail": str(exc.orig)},
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=9000,
        reload=True
    )