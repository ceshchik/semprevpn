from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks.factory import MenuCB, SubscriptionCB
from bot.database.repositories.subscription import SubscriptionRepository
from bot.database.models import User, Subscription, GlobalSettings
from bot.keyboards.inline import get_back_menu
from bot.handlers.catalog import PREDEFINED_TARIFFS
from bot.config import Settings

router = Router(name="my_subscriptions_router")

@router.callback_query(MenuCB.filter(F.action == "subscriptions"))
async def my_subscriptions(query: CallbackQuery, db_user: User, sub_repo: SubscriptionRepository, session: AsyncSession):
    subs = await sub_repo.get_by_user_id(db_user.id)
    if not subs:
        text = "у тебя пока нет активных подписок"
        return await query.message.edit_text(text, reply_markup=get_back_menu())
        
    res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    gs = res.scalar_one_or_none()
    allow_refunds = gs.allow_refunds if gs else False
    
    text = "твои подписки:\n\n"
    active_sub = None
    for sub in subs:
        text += f"◦ {sub.tariff_slug} — до {sub.expires_at.strftime('%d.%m.%Y')}\n"
        if sub.subscription_url:
            text += f"  Ссылка 1: <code>{sub.subscription_url}</code>\n"
        if sub.subscription_url_2:
            text += f"  Ссылка 2: <code>{sub.subscription_url_2}</code>\n"
        text += f"  Устройств: {sub.device_count}\n"
        text += f"  Статус: {sub.status}\n\n"
        if sub.status == "active":
            active_sub = sub
            
    builder = InlineKeyboardBuilder()
    
    if active_sub:
        builder.button(text="◦ улучшить", callback_data=SubscriptionCB(id=active_sub.id, action="upgrade").pack())
        
        days_since_start = (datetime.now() - active_sub.started_at).days
        if days_since_start <= 2 or allow_refunds:
            builder.button(text="◦ возврат средств", callback_data=SubscriptionCB(id=active_sub.id, action="refund").pack())
            
    builder.button(text="‹ назад", callback_data=MenuCB(action="back_to_main").pack())
    builder.adjust(1)
            
    await query.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(SubscriptionCB.filter(F.action == "upgrade"))
async def upgrade_sub(query: CallbackQuery, callback_data: SubscriptionCB, sub_repo: SubscriptionRepository):
    sub = await sub_repo.get(callback_data.id)
    if not sub or sub.status != "active":
        return await query.answer("Подписка не найдена или неактивна")
        
    current_tariff = PREDEFINED_TARIFFS.get(sub.tariff_slug)
    if not current_tariff:
        return await query.answer("Текущий тариф не найден")
        
    builder = InlineKeyboardBuilder()
    has_options = False
    
    for slug, tariff in PREDEFINED_TARIFFS.items():
        if tariff['price'] > current_tariff['price']:
            builder.button(text=f"до {tariff['name']}", callback_data=f"upg_confirm_{sub.id}_{slug}")
            has_options = True
            
    if not has_options:
        return await query.answer("У тебя уже максимальный тариф", show_alert=True)
        
    builder.button(text="‹ назад", callback_data=MenuCB(action="subscriptions").pack())
    builder.adjust(1)
    
    await query.message.edit_text("выбери тариф для улучшения (оплата пропорционально остатку дней):", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("upg_confirm_"))
async def confirm_upgrade(query: CallbackQuery, sub_repo: SubscriptionRepository, session: AsyncSession):
    parts = query.data.split("_")
    sub_id = int(parts[2])
    new_slug = parts[3]
    
    sub = await sub_repo.get(sub_id)
    if not sub or sub.status != "active":
        return await query.answer("Подписка неактивна")
        
    current_tariff = PREDEFINED_TARIFFS.get(sub.tariff_slug)
    new_tariff = PREDEFINED_TARIFFS.get(new_slug)
    
    remaining_days = max(0, (sub.expires_at - datetime.now()).days)
    diff_price = new_tariff['price'] - current_tariff['price']
    upgrade_cost = int((diff_price / 30.0) * remaining_days)
    
    builder = InlineKeyboardBuilder()
    if upgrade_cost > 0:
        builder.button(text=f"◦ оплатить {upgrade_cost} ₽", callback_data=f"upg_pay_{sub.id}_{new_slug}_{upgrade_cost}")
    else:
        builder.button(text="◦ улучшить бесплатно", callback_data=f"upg_pay_{sub.id}_{new_slug}_0")
        
    builder.button(text="‹ отмена", callback_data=SubscriptionCB(id=sub.id, action="upgrade").pack())
    builder.adjust(1)
    
    text = f"улучшение до {new_tariff['name']}\nостаток дней: {remaining_days}\nк доплате: {upgrade_cost} ₽"
    await query.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("upg_pay_"))
async def execute_upgrade(query: CallbackQuery, sub_repo: SubscriptionRepository, session: AsyncSession):
    parts = query.data.split("_")
    sub_id = int(parts[2])
    new_slug = parts[3]
    cost = int(parts[4])
    
    sub = await sub_repo.get(sub_id)
    if not sub or sub.status != "active":
        return await query.answer("Ошибка")
        
    # Заглушка: считаем что оплата прошла мгновенно (в реальности нужен вызов платеги)
    sub.tariff_slug = new_slug
    await session.commit()
    
    await query.answer("Тариф успешно улучшен!", show_alert=True)
    
    # Возвращаемся в мои подписки
    builder = InlineKeyboardBuilder()
    builder.button(text="к подпискам", callback_data=MenuCB(action="subscriptions").pack())
    await query.message.edit_text("Тариф улучшен.", reply_markup=builder.as_markup())


@router.callback_query(SubscriptionCB.filter(F.action == "refund"))
async def refund_sub(query: CallbackQuery, callback_data: SubscriptionCB, sub_repo: SubscriptionRepository, session: AsyncSession):
    sub = await sub_repo.get(callback_data.id)
    if not sub or sub.status != "active":
        return await query.answer("Подписка неактивна")
        
    # Удаляем информацию о подписке (отвязываем от заказа)
    from bot.database.models import Order
    from sqlalchemy import update
    await session.execute(update(Order).where(Order.subscription_id == sub.id).values(subscription_id=None))
    
    await sub_repo.delete(sub.id)
    await session.commit()
    
    await query.answer("Средства будут возвращены, подписка отменена.", show_alert=True)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="в меню", callback_data=MenuCB(action="back_to_main").pack())
    await query.message.edit_text("Подписка отменена и оформлен возврат.", reply_markup=builder.as_markup())
