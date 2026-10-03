import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import Settings
from bot.handlers import start, catalog, purchase, my_subscriptions, profile, support, admin, common
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.database.engine import create_engine, create_session_factory
from bot.database.models import Base
from bot.services.remnawave import RemnawaveClient
from bot.services.payment import StubPaymentProvider

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s · %(name)s · %(message)s")
    
    settings = Settings()
    
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    
    # Автоматическое создание таблиц для тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Services
    remnawave = RemnawaveClient(settings.remnawave_url, settings.remnawave_api_token)
    payment = StubPaymentProvider()
    
    # Middlewares
    dp.update.middleware(DatabaseMiddleware(session_factory))
    dp.message.middleware(ThrottlingMiddleware())
    
    # Inject services
    dp["remnawave"] = remnawave
    dp["payment"] = payment
    dp["settings"] = settings
    
    # Routers
    dp.include_routers(
        start.router,
        catalog.router,
        purchase.router,
        my_subscriptions.router,
        profile.router,
        support.router,
        admin.router,
        common.router,
    )
    
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
