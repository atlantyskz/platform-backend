from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.repositories.balance import BalanceRepository
from src.core.exceptions import NotFoundException


class BalanceController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.balance_repository = BalanceRepository(session)
        self.organization_repository = OrganizationRepository(session)
        self.user_repository = UserRepository(session)
        
    
    async def get_balance(self,user_id:int):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        organization = await self.organization_repository.get_user_organization(user_id)
        print(organization)
        balance = await self.balance_repository.get_balance(organization.id)
        if balance is None:
            balance = await self.balance_repository.create_balance({"organization_id":organization.id,"atl_tokens":0})
        return {"balance":balance.atl_tokens}