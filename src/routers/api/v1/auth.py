from fastapi import APIRouter,Depends
from src.core.middlewares.auth_middleware import JWTBearer
from src.controllers.auth import AuthController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from src.core.middlewares.auth_middleware import get_current_user


auth_router = APIRouter(prefix='/api/v1/auth',tags=['Auth'])

@auth_router.post('/register')
async def register(register_user_request:RegisterUserRequest,auth_controller:AuthController = Depends(Factory.get_auth_controller)):
    return await auth_controller.create_user(email=register_user_request.email,password=register_user_request.password)

@auth_router.get('/get',)
async def get_by_email(
    auth_controller:AuthController = Depends(Factory.get_auth_controller),
    current_user:dict = Depends(get_current_user)
):
    return current_user

@auth_router.post("/login")
async def login_user(
    login_user_request: LoginUserRequest,
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
) -> Token:
    return await auth_controller.login(
        email=login_user_request.email, password=login_user_request.password
    )


@auth_router.get('/current_user')
async def get_current_user(
    auth_controller: AuthController = Depends(Factory.get_auth_controller),
    current_user:dict = Depends(get_current_user)

):
    user_id = current_user.get('sub')
    return await auth_controller.get_current_user(user_id)