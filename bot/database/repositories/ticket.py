from typing import Optional
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bot.database.repositories.base import BaseRepository
from bot.database.models import Ticket, TicketMessage

class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session):
        super().__init__(session, Ticket)

    async def get_by_user_id(self, user_id: int) -> Sequence[Ticket]:
        result = await self.session.execute(
            select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.id.desc())
        )
        return result.scalars().all()
        
    async def get_with_messages(self, ticket_id: int) -> Optional[Ticket]:
        result = await self.session.execute(
            select(Ticket).options(selectinload(Ticket.messages)).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

class TicketMessageRepository(BaseRepository[TicketMessage]):
    def __init__(self, session):
        super().__init__(session, TicketMessage)
