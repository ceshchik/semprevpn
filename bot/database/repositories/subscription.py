from typing import Sequence
from sqlalchemy import select
from bot.database.repositories.base import BaseRepository
from bot.database.models import Subscription

class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, session):
        super().__init__(session, Subscription)

    async def get_by_user_id(self, user_id: int) -> Sequence[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.id.desc())
        )
        return result.scalars().all()

    async def get_active_by_user_id(self, user_id: int) -> Sequence[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
        )
        return result.scalars().all()
