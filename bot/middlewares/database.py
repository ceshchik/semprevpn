from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.database.repositories.user import UserRepository
from bot.database.repositories.subscription import SubscriptionRepository
from bot.database.repositories.order import OrderRepository
from bot.database.repositories.ticket import TicketRepository, TicketMessageRepository
from bot.database.repositories.promo import PromoCodeRepository

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            # Инициализация репозиториев
            user_repo = UserRepository(session)
            
            # Если это Message или CallbackQuery, мы можем сразу получить/создать юзера
            user = None
            tg_user = data.get("event_from_user")
            if tg_user:
                user = await user_repo.create_user_if_not_exists(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name
                )
                await session.commit()
            
            data["session"] = session
            data["db_user"] = user
            data["user_repo"] = user_repo
            data["sub_repo"] = SubscriptionRepository(session)
            data["order_repo"] = OrderRepository(session)
            data["ticket_repo"] = TicketRepository(session)
            data["ticket_msg_repo"] = TicketMessageRepository(session)
            data["promo_repo"] = PromoCodeRepository(session)
            
            result = await handler(event, data)
            
            # Коммитим после успешного выполнения хендлера
            await session.commit()
            
            return result
