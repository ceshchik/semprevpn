from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks.factory import MenuCB, TariffCB

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="◦ тарифы", callback_data=MenuCB(action="tariffs"))
    builder.button(text="◦ мои подписки", callback_data=MenuCB(action="subscriptions"))
    builder.button(text="◦ поддержка", callback_data=MenuCB(action="support"))
    builder.button(text="◦ профиль", callback_data=MenuCB(action="profile"))
    builder.adjust(2)
    return builder.as_markup()

def get_tariffs_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="◦ lite", callback_data=TariffCB(slug="lite", action="view"))
    builder.button(text="◦ base", callback_data=TariffCB(slug="base", action="view"))
    builder.button(text="◦ comfort", callback_data=TariffCB(slug="comfort", action="view"))
    builder.button(text="‹ назад", callback_data=MenuCB(action="back_to_main"))
    builder.adjust(1)
    return builder.as_markup()

def get_back_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="‹ назад", callback_data=MenuCB(action="back_to_main"))
    return builder.as_markup()
