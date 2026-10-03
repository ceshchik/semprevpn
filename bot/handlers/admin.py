from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database.models import User, PromoCode, TicketMessage
from bot.database.repositories.promo import PromoCodeRepository
from bot.database.repositories.ticket import TicketRepository, TicketMessageRepository
from bot.database.repositories.user import UserRepository
from bot.config import Settings
from bot.states.admin import AdminPromoState, AdminTicketState
from bot.callbacks.factory import TicketCB
from aiogram.types import CallbackQuery
from aiogram import Bot

router = Router(name="admin_router")

def is_admin(db_user: User, settings: Settings) -> bool:
    return db_user.telegram_id in settings.admin_ids

@router.message(Command("admin"))
async def admin_panel(message: Message, db_user: User, settings: Settings):
    if not is_admin(db_user, settings):
        return
        
    await message.answer(
        "Админ-панель\n\n"
        "Доступные команды:\n"
        "/promo - создать промокод\n"
        "/refunds - включить/выключить временное разрешение на возврат всем\n"
    )

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import GlobalSettings

@router.message(Command("refunds"))
async def cmd_refunds(message: Message, db_user: User, settings: Settings, session: AsyncSession):
    if not is_admin(db_user, settings):
        return
        
    res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    gs = res.scalar_one_or_none()
    
    if not gs:
        gs = GlobalSettings(id=1, allow_refunds=False)
        session.add(gs)
        
    gs.allow_refunds = not gs.allow_refunds
    await session.commit()
    
    status_text = "ВКЛЮЧЕНО" if gs.allow_refunds else "ВЫКЛЮЧЕНО"
    await message.answer(f"Временное разрешение на возврат для всех пользователей: {status_text}")

@router.message(Command("promo"))
async def cmd_promo(message: Message, db_user: User, settings: Settings, state: FSMContext):
    if not is_admin(db_user, settings):
        return
    await message.answer("Введите код промокода (на английском, без пробелов, например: SALE20):")
    await state.set_state(AdminPromoState.waiting_for_code)

@router.message(AdminPromoState.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip().lower())
    await message.answer("Введите процент скидки (от 1 до 100):")
    await state.set_state(AdminPromoState.waiting_for_discount)

@router.message(AdminPromoState.waiting_for_discount)
async def process_promo_discount(message: Message, state: FSMContext):
    try:
        discount = int(message.text.strip())
        if not (1 <= discount <= 100):
            raise ValueError
    except ValueError:
        return await message.answer("Пожалуйста, введите корректное число от 1 до 100.")
        
    await state.update_data(discount=discount)
    await message.answer("Введите максимальное количество использований (0 - без ограничений):")
    await state.set_state(AdminPromoState.waiting_for_max_uses)

@router.message(AdminPromoState.waiting_for_max_uses)
async def process_promo_max_uses(message: Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
        if max_uses < 0:
            raise ValueError
    except ValueError:
        return await message.answer("Пожалуйста, введите корректное число (0 или больше).")
        
    await state.update_data(max_uses=max_uses)
    await message.answer("Введите срок действия промокода в днях (0 - бессрочный):")
    await state.set_state(AdminPromoState.waiting_for_days_valid)

@router.message(AdminPromoState.waiting_for_days_valid)
async def process_promo_days(message: Message, state: FSMContext, promo_repo: PromoCodeRepository):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except ValueError:
        return await message.answer("Пожалуйста, введите корректное число (0 или больше).")
        
    data = await state.get_data()
    code = data['code']
    discount = data['discount']
    max_uses = data['max_uses']
    
    expires_at = datetime.now() + timedelta(days=days) if days > 0 else None
    
    # Проверяем, существует ли уже
    existing = await promo_repo.get_by_code(code)
    if existing:
        return await message.answer(f"Промокод {code} уже существует.")
        
    promo = PromoCode(
        code=code,
        discount_percent=discount,
        max_uses=max_uses,
        expires_at=expires_at
    )
    await promo_repo.add(promo)
    
    msg = f"✅ Промокод создан!\n\nКод: {code}\nСкидка: {discount}%\n"
    msg += f"Использований: {'безлимит' if max_uses == 0 else max_uses}\n"
    msg += f"Действует до: {expires_at.strftime('%d.%m.%Y %H:%M') if expires_at else 'бессрочно'}"
    
    await message.answer(msg)
    await state.clear()

@router.callback_query(TicketCB.filter(F.action == "reply"))
async def admin_reply_to_ticket(query: CallbackQuery, callback_data: TicketCB, state: FSMContext, db_user: User, settings: Settings):
    if not is_admin(db_user, settings):
        return await query.answer("Нет прав", show_alert=True)
    await state.update_data(ticket_id=callback_data.id)
    await query.message.answer(f"Введите ответ на тикет #{callback_data.id}:")
    await state.set_state(AdminTicketState.waiting_for_reply)

@router.message(AdminTicketState.waiting_for_reply)
async def process_ticket_reply(
    message: Message,
    state: FSMContext,
    db_user: User,
    settings: Settings,
    bot: Bot,
    ticket_repo: TicketRepository,
    ticket_msg_repo: TicketMessageRepository,
    user_repo: UserRepository
):
    if not is_admin(db_user, settings):
        return
        
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    if not ticket_id:
        return await state.clear()
        
    ticket = await ticket_repo.get(ticket_id)
    if not ticket:
        await message.answer("Тикет не найден.")
        return await state.clear()
        
    ticket_author = await user_repo.get(ticket.user_id)
    if not ticket_author:
        await message.answer("Пользователь не найден.")
        return await state.clear()
        
    # Save reply to DB
    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_type="admin",
        sender_id=message.from_user.id,
        text=message.text or "Медиа/Файл"
    )
    await ticket_msg_repo.add(msg)
    
    # Send to user
    try:
        await bot.send_message(
            ticket_author.telegram_id,
            f"Ответ поддержки (Тикет #{ticket.id}):\n\n{msg.text}"
        )
        await message.answer("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить ответ пользователю: {e}")
        
    await state.clear()
