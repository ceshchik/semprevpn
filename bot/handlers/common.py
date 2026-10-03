from aiogram import Router
from aiogram.types import Message

router = Router(name="common_router")

@router.message()
async def fallback_handler(message: Message):
    pass
