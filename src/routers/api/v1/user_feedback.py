

from fastapi import APIRouter,Depends
from src.schemas.requests.user_feedback import UserFeedbackRequest
from src.models.role import RoleEnum
from src.controllers.user_feedback import UserFeedbackController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *

from src.core.middlewares.auth_middleware import get_current_user,require_roles


user_feedback_router = APIRouter(prefix='/api/v1/user_feedback',tags=['USER FEEDBACK'])

@user_feedback_router.post("/")
async def create_feedback(
    user_feedback_request: UserFeedbackRequest,
    current_user:dict = Depends(get_current_user),
    user_feedback_controller :UserFeedbackController = Depends(Factory.get_user_feedback_controller)):
    return await user_feedback_controller.create_feedback(current_user.get('sub'),user_feedback_request.model_dump())