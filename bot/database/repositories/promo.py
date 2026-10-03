from typing import Optional
from sqlalchemy import select
from bot.database.repositories.base import BaseRepository
from bot.database.models import PromoCode

class PromoCodeRepository(BaseRepository[PromoCode]):
    def __init__(self, session):
        super().__init__(session, PromoCode)

    async def get_by_code(self, code: str) -> Optional[PromoCode]:
        result = await self.session.execute(
            select(PromoCode).where(PromoCode.code == code)
        )
        return result.scalar_one_or_none()
