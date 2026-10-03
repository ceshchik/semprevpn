from typing import Optional
from sqlalchemy import select
from bot.database.repositories.base import BaseRepository
from bot.database.models import User

class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create_user_if_not_exists(self, telegram_id: int, username: Optional[str], first_name: Optional[str]) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name)
            user = await self.add(user)
        return user
