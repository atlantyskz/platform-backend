from src.core.exceptions import NotFoundException
from src.repositories.user_feedback import UserFeedbackRepository
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserFeedbackController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.feedback_repo =UserFeedbackRepository(self.session)
        self.user_repo = UserRepository(self.session)

    async def create_feedback(self,user_id,attributes:dict):
        async with self.session.begin():
            user = await self.user_repo.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException('User Not found')
            await self.feedback_repo.create({
                'user_id':user.id,
                'user_email':user.email,
                **attributes
            })
            return {'success':True}
