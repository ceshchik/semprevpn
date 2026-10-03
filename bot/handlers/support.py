from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.callbacks.factory import MenuCB
from bot.database.models import User, Ticket, TicketMessage
from bot.database.repositories.ticket import TicketRepository, TicketMessageRepository
from bot.states.support import SupportState
from bot.utils.texts import SUPPORT_GREETING, SUPPORT_TICKET_CREATED
from bot.config import Settings
from bot.keyboards.inline import get_back_menu

router = Router(name="support_router")

@router.callback_query(MenuCB.filter(F.action == "support"))
async def support_menu(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text(SUPPORT_GREETING, reply_markup=get_back_menu())
    await state.set_state(SupportState.waiting_for_message)

@router.message(SupportState.waiting_for_message)
async def process_support_message(
    message: Message, 
    state: FSMContext, 
    db_user: User, 
    ticket_repo: TicketRepository,
    ticket_msg_repo: TicketMessageRepository,
    bot: Bot,
    settings: Settings
):
    ticket = Ticket(
        user_id=db_user.id,
        subject=f"Обращение от {db_user.telegram_id}"
    )
    ticket = await ticket_repo.add(ticket)
    
    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_type="user",
        sender_id=message.from_user.id,
        text=message.text or "Медиа/Файл"
    )
    await ticket_msg_repo.add(msg)
    
    await message.answer(SUPPORT_TICKET_CREATED)
    await state.clear()
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from bot.callbacks.factory import TicketCB
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Ответить", callback_data=TicketCB(id=ticket.id, action="reply"))
    kb = builder.as_markup()
    
    if settings.support_chat_id:
        await bot.send_message(
            settings.support_chat_id,
            f"Новый тикет #{ticket.id} от {message.from_user.id}:\n\n{msg.text}",
            reply_markup=kb
        )
    else:
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"Новый тикет #{ticket.id} от {message.from_user.id}:\n\n{msg.text}",
                    reply_markup=kb
                )
            except Exception:
                pass
