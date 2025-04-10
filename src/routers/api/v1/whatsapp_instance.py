from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from src.controllers.whatsapp_instance import WhatsappInstanceController
from src.controllers.whatsapp_webhook_controller import WhatsappWebhookController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user, require_roles
from src.models import RoleEnum

router = APIRouter(prefix="/api/v1/whatsapp-integration", tags=["WHATSAPP"])


@router.post("/create-instance")
async def create_instance(
    whatsapp_instance: WhatsappInstanceController = Depends(Factory.get_whatsapp_instance_controller),
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await whatsapp_instance.add_whatsapp_instance(user_id=user_id)


@router.get("/my-instance")
async def my_instance(
    whatsapp_instance: WhatsappInstanceController = Depends(Factory.get_whatsapp_instance_controller),
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await whatsapp_instance.get_user_instance(user_id=user_id)


@router.get("/show-qr")
async def show_qr_code(
    whatsapp_instance: WhatsappInstanceController = Depends(Factory.get_whatsapp_instance_controller),
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    result = await whatsapp_instance.get_instance_qr_code(user_id=user_id)
    base64_img = result["message"]
    return {"detail": f"data:image/png;base64,{base64_img}"}


@router.get("/organization-instances")
@require_roles([RoleEnum.SUPER_ADMIN.value, RoleEnum.ADMIN.value])
async def get_admin_whatsapp_instances(
    whatsapp_instance: WhatsappInstanceController = Depends(Factory.get_whatsapp_instance_controller),
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await whatsapp_instance.get_organization_instances(user_id)


@router.get("/current-instance")
async def get_current_instance(
    whatsapp_instance: WhatsappInstanceController = Depends(Factory.get_whatsapp_instance_controller),
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await whatsapp_instance.get_current_instance(user_id=user_id)


@router.post("/set-current-instance")
async def set_current_instance(
    whatsapp_instance_id: int,
    whatsapp_instance: WhatsappInstanceController = Depends(Factory.get_whatsapp_instance_controller),
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await whatsapp_instance.set_current_instance(user_id=user_id, whatsapp_instance_id=whatsapp_instance_id)


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    webhook_controller: WhatsappWebhookController = Depends(Factory.get_whatsapp_webhook_controller),
):
    data = await request.json()
    result = await webhook_controller.handle_incoming_webhook(data)
    return JSONResponse(result, status_code=200 if "error" not in result else 400)
