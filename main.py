import httpx
from fastapi import FastAPI
from fastapi import staticfiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqladmin import Admin, ModelView

from src.core.databases import session_manager
from src.core.middlewares.auth_admin import authentication_backend
from src.core.store import lifespan
from src.models import sql_admin_models_list
from src.routers.api.v1.assistant import assistant_router
from src.routers.api.v1.auth import auth_router
from src.routers.api.v1.balance import balance_router
from src.routers.api.v1.billing import billing_router
from src.routers.api.v1.clone import clone_router
from src.routers.api.v1.hh import hh_router
from src.routers.api.v1.hr_agent import hr_agent_router
from src.routers.api.v1.interview_common_question import interview_common_question_router
from src.routers.api.v1.interview_individual_question import interview_individual_question_router
from src.routers.api.v1.organization import organization_router
from src.routers.api.v1.organization_member import organization_member_router
from src.routers.api.v1.phone_interview import phone_interview_router
from src.routers.api.v1.promo_code import promocode_router
from src.routers.api.v1.subs_router import subs_router
from src.routers.api.v1.user_feedback import user_feedback_router


def custom_openapi(app):
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
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
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
        return JSONResponse(content=app.openapi())


def create_app(create_custom_static_urls: bool = False) -> FastAPI:
    app = FastAPI(
        title="Platform Backend",
        lifespan=lifespan,
        docs_url=None if create_custom_static_urls else '/api/docs',
        redoc_url=None if create_custom_static_urls else '/api/redoc',
        openapi_url="/api/openapi.json"
    )

    app.openapi = lambda: custom_openapi(app)

    @app.get("/exceptions")
    async def send_exception(request):
        raise Exception

    app.include_router(hh_router)
    app.include_router(auth_router)
    app.include_router(hr_agent_router)
    app.include_router(organization_router)
    app.include_router(organization_member_router)
    app.include_router(assistant_router)
    app.include_router(user_feedback_router)
    app.include_router(billing_router)
    app.include_router(balance_router)
    app.include_router(clone_router)
    app.include_router(phone_interview_router)
    app.include_router(interview_common_question_router)
    app.include_router(interview_individual_question_router)
    app.include_router(subs_router)
    app.include_router(promocode_router)

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
    return app


app = create_app(create_custom_static_urls=True)
app.mount("/static", staticfiles.StaticFiles(directory="collected_static"), name="static")

admin = Admin(app, session_manager._engine, authentication_backend=authentication_backend)

for model in sql_admin_models_list:
    # Динамически создаем класс ModelView
    class ModelViewClass(ModelView, model=model):
        column_list = [c.name for c in model.__table__.columns]


    admin.add_view(ModelViewClass)
from sqlalchemy.exc import IntegrityError, DBAPIError

TELEGRAM_BOT_URL = "http://telegram-bot:9005/send_alert"  # Docker service name


# Глобальный обработчик IntegrityError
@app.exception_handler(IntegrityError)
async def database_error_handler(request, exc: IntegrityError):
    error_message = f"🚨 *Ошибка сервера:* {exc}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TELEGRAM_BOT_URL, data={"error_message": error_message})
            print(response.json())
        except Exception as e:
            print(f"Failed to notify Telegram bot: {e}")

    return JSONResponse(
        status_code=500,
        content={"error": "Database Error", "detail": str(exc.orig)},
    )


@app.exception_handler(DBAPIError)
async def database_error_handler(request, exc: DBAPIError):
    error_message = f"🚨 *Ошибка сервера:* {exc}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TELEGRAM_BOT_URL, data={"error_message": error_message})
            print(response.json())  # Debugging
        except Exception as e:
            print(f"Failed to notify Telegram bot: {e}")

    return JSONResponse(
        status_code=500,
        content={"error": "Database Error", "detail": str(exc.orig)},
    )


@app.exception_handler(Exception)
async def database_error_handler(request, exc: Exception):
    error_message = f"🚨 *Ошибка сервера:* {exc}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TELEGRAM_BOT_URL, data={"error_message": error_message})
            print(response.json())  # Debugging
        except Exception as e:
            print(f"Failed to notify Telegram bot: {e}")

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=9000,
        reload=True,
        forwarded_allow_ips='*',
        proxy_headers=True
    )
