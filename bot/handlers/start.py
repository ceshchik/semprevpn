from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import get_main_menu
from bot.utils.texts import WELCOME_TEXT
from bot.callbacks.factory import MenuCB
from bot.database.models import User

router = Router(name="start_router")

@router.message(CommandStart())
async def start_cmd(message: Message, db_user: User, state: FSMContext):
    """Приветствие и регистрация (происходит в middleware)."""
    # deep-link логику можно реализовать здесь, проверяя args у команды /start
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu())
    try:
        await message.delete()
    except Exception:
        pass

@router.callback_query(MenuCB.filter(F.action == "back_to_main"))
async def back_to_main_cb(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text(WELCOME_TEXT, reply_markup=get_main_menu())
