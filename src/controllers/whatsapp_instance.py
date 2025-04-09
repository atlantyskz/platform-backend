from src import models, repositories
from src.core import exceptions
from src.services import green_api_cli


class WhatsappInstanceController:
    def __init__(self, session):
        self.session = session
        self.user_repo = repositories.UserRepository(session)
        self.org_repo = repositories.OrganizationRepository(session)
        self.org_sub_repo = repositories.OrganizationSubscriptionRepository(session)
        self.instance_repo = repositories.WhatsappInstanceRepository(session)
        self.association_repo = repositories.WhatsappInstanceAssociationRepository(session)
        self.green_api = green_api_cli.GreenApiCli()
        self.current_instance_repo = repositories.CurrentWhatsappInstanceRepository(session)

    async def add_whatsapp_instance(self, user_id: int):
        user = await self.user_repo.get_by_user_id(user_id)
        if not user:
            raise exceptions.NotFoundException("User not found")

        organization = await self.org_repo.get_user_organization(user_id)
        if not organization:
            raise exceptions.NotFoundException("Organization not found")

        org_sub = await self.org_sub_repo.organization_active_subscription(organization.id)
        if not org_sub:
            raise exceptions.BadRequestException("Active subscription required to connect instance")

        org_instances = await self.instance_repo.get_all_by_organization(organization.id, False)
        if len(org_instances) >= org_sub.subscription_plan.limit_members:
            raise exceptions.BadRequestException("Instance limit for your plan exceeded")

        async def create_instance():
            return await self.green_api.create_instance({"email": user.email})

        if user.role.name == models.RoleEnum.ADMIN.value or user.role.name == models.RoleEnum.SUPER_ADMIN.value:
            existing_primary = await self.instance_repo.get_by_organization_id(organization.id)
            if existing_primary:
                raise exceptions.BadRequestException("Organization already has a shared WhatsApp instance")

            response = await create_instance()
            if not response.get("success"):
                raise exceptions.BadRequestException(f"Green API Error: {response.get('error')}")

            created = await self.instance_repo.add_whatsapp_instance(
                data=repositories.WhatsappInstanceDTO(
                    instance_name=user.email,
                    instance_id=str(response["instance_id"]),
                    instance_token=response["instance_token"],
                    is_primary=True,
                    instance_type=repositories.InstanceTypeEnum.SHARED,
                    organization_id=organization.id,
                )
            )

        elif user.role.name == models.RoleEnum.EMPLOYER.value:
            personal_instance = await self.association_repo.user_whatsapp_instance(user_id, organization.id)
            if personal_instance:
                raise exceptions.BadRequestException("User already has a personal WhatsApp instance")

            response = await create_instance()
            if not response.get("success"):
                raise exceptions.BadRequestException(f"Green API Error: {response.get('error')}")

            created = await self.instance_repo.add_whatsapp_instance(
                data=repositories.WhatsappInstanceDTO(
                    instance_name=user.email,
                    instance_id=response["instance_id"],
                    instance_token=response["instance_token"],
                    is_primary=False,
                    instance_type=repositories.InstanceTypeEnum.PERSONAL,
                    organization_id=organization.id,
                )
            )

        else:
            raise exceptions.BadRequestException("Invalid user role")

        await self.association_repo.add_sub_instance(
            data=repositories.WhatsappInstanceAssociation(
                user_id=user_id,
                whatsapp_instance_id=created.id
            )
        )
        await self.current_instance_repo.set_current_instance(user_id, created.id)
        await self.session.commit()

        return {"detail": "WhatsApp instance created successfully"}

    async def get_organization_instances(self, user_id: int):
        user = await self.user_repo.get_by_user_id(user_id)
        organization = await self.org_repo.get_user_organization(user_id)
        if not organization:
            raise exceptions.NotFoundException("Organization not found")

        if user.role.name == models.RoleEnum.ADMIN.value:
            return await self.instance_repo.get_all_by_organization(organization.id, True)

        shared_instance = await self.instance_repo.get_by_organization_id(organization.id)

        personal_associated_instance = await self.association_repo.user_whatsapp_instance(
            user_id=user_id,
            organization_id=organization.id
        )

        personal_instance = None
        if personal_associated_instance:
            personal_instance = await self.instance_repo.get_by_instance_id(
                personal_associated_instance.whatsapp_instance_id
            )

        return {
            "shared_instance": shared_instance,
            "personal_instance": personal_instance
        }

    async def get_instance_qr_code(self, user_id: int):
        user = await self.user_repo.get_by_user_id(user_id)
        if not user:
            raise exceptions.NotFoundException("User not found")

        organization = await self.org_repo.get_user_organization(user_id)
        if not organization:
            raise exceptions.NotFoundException("Organization not found")

        db_instance = await self.instance_repo.get_by_organization_id(organization.id)
        if not db_instance:
            raise exceptions.NotFoundException("Instance not found")

        if user.role.name == models.RoleEnum.EMPLOYER.value:
            user_instance = await self.association_repo.user_whatsapp_instance(user_id, organization.id)
            if user_instance:
                raise exceptions.BadRequestException("User already has a personal WhatsApp instance")

        state_resp = await self.green_api.get_instance_state(
            db_instance.instance_id,
            db_instance.instance_token
        )
        state = state_resp.get("state_instance")
        if state in ("starting",):
            await self.green_api.reboot_instance(db_instance.instance_id, db_instance.instance_token)

        state = state_resp.get("state_instance")
        if state in ("notAuthorized", "sleepMode"):
            return await self.green_api.get_qr_code(db_instance.instance_id, db_instance.instance_token)

        if state == "authorized":
            raise exceptions.BadRequestException("WhatsApp instance is already connected")

        raise exceptions.BadRequestException(f"Instance in unexpected state: {state}")

    async def get_user_instance(self, user_id: int):
        organization = await self.org_repo.get_user_organization(user_id)
        if not organization:
            raise exceptions.NotFoundException("Organization not found")

        sub_instance = await self.association_repo.user_whatsapp_instance(user_id, organization.id)
        if not sub_instance:
            raise exceptions.NotFoundException("Sub instance not found")

        state_resp = await self.green_api.get_instance_state(
            sub_instance.instance_id,
            sub_instance.instance_token
        )
        if not state_resp.get("success"):
            raise exceptions.BadRequestException(f"Error fetching instance state: {state_resp.get('error')}")

        state = state_resp.get("state_instance")

        return {
            "instance_id": sub_instance.whatsapp_instance_id,
            "instance_token": sub_instance.instance_token,
            "state": state
        }

    async def set_current_instance(self, user_id: int, whatsapp_instance_id: int):
        instance = await self.instance_repo.get_by_id(whatsapp_instance_id)
        if not instance:
            raise exceptions.NotFoundException("WhatsApp instance not found")

        await self.current_instance_repo.set_current_instance(user_id, whatsapp_instance_id)
        await self.session.commit()
        return {"detail": "Current instance set successfully"}

    async def get_current_instance(self, user_id: int):
        instance_id = await self.current_instance_repo.get_current_instance_id(user_id)
        if not instance_id:
            raise exceptions.NotFoundException("Current instance not set")

        instance = await self.instance_repo.get_by_id(instance_id)
        if not instance:
            raise exceptions.NotFoundException("WhatsApp instance not found")

        return instance
