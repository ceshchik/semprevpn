from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.callbacks.factory import MenuCB
from bot.database.repositories.subscription import SubscriptionRepository
from bot.database.models import User
from bot.utils.texts import PROFILE_TEXT
from bot.keyboards.inline import get_back_menu

router = Router(name="profile_router")

@router.callback_query(MenuCB.filter(F.action == "profile"))
async def profile(query: CallbackQuery, db_user: User, sub_repo: SubscriptionRepository):
    subs = await sub_repo.get_by_user_id(db_user.id)
    active_subs = [s for s in subs if s.status == "active"]
    
    reg_date = db_user.created_at.strftime("%d.%m.%Y")
    
    text = PROFILE_TEXT.format(
        telegram_id=db_user.telegram_id,
        email=db_user.email if db_user.email else "не привязан",
        registered_at=reg_date,
        subs_count=f"{len(active_subs)} / {len(subs)}",
        orders_history="◦ пусто"  # TODO: Добавить историю заказов
    )
    await query.message.edit_text(text, reply_markup=get_back_menu())
