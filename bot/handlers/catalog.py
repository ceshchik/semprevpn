from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from bot.callbacks.factory import MenuCB, TariffCB
from bot.keyboards.inline import get_tariffs_menu
from bot.utils.texts import TARIFFS_CATALOG

router = Router(name="catalog_router")

PREDEFINED_TARIFFS = {
    "lite": {"name": "lite", "devices": 2, "days": 30, "price": 149, "desc": "2 устройства · 30 дней · безлимит"},
    "base": {"name": "base", "devices": 2, "days": 30, "price": 249, "desc": "2 устройства · 30 дней · безлимит"},
    "comfort": {"name": "comfort", "devices": 2, "days": 30, "price": 399, "desc": "2 устройства · 30 дней · безлимит"},
}

@router.callback_query(MenuCB.filter(F.action == "tariffs"))
async def show_catalog(query: CallbackQuery, state: FSMContext):
    await state.clear()
    text = f"{TARIFFS_CATALOG}\n\n"
    for slug, tariff in PREDEFINED_TARIFFS.items():
        text += f"◦ {tariff['name']} — {tariff['desc']} — {tariff['price']} ₽\n"
    
    await query.message.edit_text(text, reply_markup=get_tariffs_menu())

@router.callback_query(TariffCB.filter(F.action == "view"))
async def view_tariff(query: CallbackQuery, callback_data: TariffCB):
    tariff = PREDEFINED_TARIFFS.get(callback_data.slug)
    if not tariff:
        return await query.answer("Тариф не найден", show_alert=True)
        
    text = f"тариф {tariff['name']}\n\n{tariff['desc']}\nцена: {tariff['price']} ₽"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◦ оформить", callback_data=TariffCB(slug=callback_data.slug, action="buy"))
    builder.button(text="‹ назад", callback_data=MenuCB(action="tariffs"))
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
