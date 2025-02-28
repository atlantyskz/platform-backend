from fastapi import APIRouter,Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
import httpx
from src.controllers.auth import AuthController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from src.core.middlewares.auth_middleware import get_current_user

from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

auth_router = APIRouter(prefix="/api/v1/auth", tags=["AUTH"])

@auth_router.get("/google")
async def google_login(
    request: Request,
    auth_controller: AuthController = Depends(Factory.get_auth_controller)
):
    return await auth_controller.google_auth(request)

@auth_router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    auth_controller: AuthController = Depends(Factory.get_auth_controller)
):
    params = {
        "code":code,
        "state":state
    }
    return await auth_controller.google_auth_callback(params)

@auth_router.post('/register')
async def register(
    register_user_request: RegisterUserRequest,
    auth_controller: AuthController = Depends(Factory.get_auth_controller)
)-> Token:
    return await auth_controller.create_user(email=register_user_request.email,password=register_user_request.password)

@auth_router.post("/login")
async def login_user(
    login_user_request: LoginUserRequest,
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
) -> Token:
    return await auth_controller.login(
        email=login_user_request.email, password=login_user_request.password
    )

@auth_router.post("/refresh_token")
async def refresh_token(
    refresh_token_request: RefreshToken, 
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
) -> Token:
    return await auth_controller.refresh_token(refresh_token_request.refresh_token)


@auth_router.get('/current_user')
async def get_current_user(
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
    current_user:dict = Depends(get_current_user)
):
    user_id = current_user.get('sub')
    return await auth_controller.get_current_user(user_id)

@auth_router.post("/verify-email", )
async def verify_email(
    verify_data: VerifyEmailRequest,
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
):
    result = await auth_controller.verify_email(verify_data.token)
    return result


@auth_router.post("/request-reset-password", summary="Request password reset")
async def request_reset_password(
    request: ResetPasswordRequest, 
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
):
    return await auth_controller.request_to_reset_password(email=request.email)

@auth_router.post("/reset-password", summary="Reset password")
async def reset_password(
    request: SetNewPassword, 
    auth_controller: AuthController = Depends(Factory.get_auth_controller),

):
    return await auth_controller.reset_password(token=request.token, new_password=request.new_password)
