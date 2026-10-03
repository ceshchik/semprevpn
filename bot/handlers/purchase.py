import time
import uuid
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.callbacks.factory import TariffCB, MenuCB, DeviceCountCB
from bot.handlers.catalog import PREDEFINED_TARIFFS
from bot.services.remnawave import RemnawaveClient
from bot.services.payment import PaymentProvider
from bot.database.models import User, Order, Subscription
from bot.database.repositories.order import OrderRepository
from bot.database.repositories.subscription import SubscriptionRepository
from bot.database.repositories.promo import PromoCodeRepository
from bot.states.purchase import PurchaseState
from bot.utils.texts import PURCHASE_SUCCESS
from bot.config import Settings

from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="purchase_router")

def get_price(tariff, devices, settings: Settings):
    extra_devices = devices - settings.default_devices
    return tariff['price'] + extra_devices * settings.extra_device_price

def build_confirm_kb(devices: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="➖", callback_data=DeviceCountCB(action="dec").pack())
    builder.button(text=f"{devices} шт.", callback_data="ignore")
    builder.button(text="➕", callback_data=DeviceCountCB(action="inc").pack())
    builder.button(text="◦ оплатить", callback_data="pay_confirm")
    builder.button(text="◦ ввести промокод", callback_data="pay_promo")
    builder.button(text="‹ отмена", callback_data=MenuCB(action="tariffs").pack())
    builder.adjust(3, 1, 1, 1)
    return builder.as_markup()

@router.callback_query(TariffCB.filter(F.action == "buy"))
async def confirm_purchase(query: CallbackQuery, callback_data: TariffCB, state: FSMContext, db_user: User, sub_repo: SubscriptionRepository, settings: Settings):
    active_subs = await sub_repo.get_active_by_user_id(db_user.id)
    if active_subs:
        return await query.answer("купить новую подписку пока что невозможно, у тебя уже есть активная", show_alert=True)
        
    tariff = PREDEFINED_TARIFFS.get(callback_data.slug)
    if not tariff:
        return await query.answer("Тариф не найден", show_alert=True)
        
    devices = settings.default_devices
    base_price = get_price(tariff, devices, settings)
    
    await state.update_data(tariff_slug=callback_data.slug, devices=devices, final_price=base_price, base_price=base_price, promo_id=None, promo_discount=0)
    
    text = f"подтверждение\n\nтариф: {tariff['name']}\nустройств: {devices}\nсумма: {base_price} ₽"
    await query.message.edit_text(text, reply_markup=build_confirm_kb(devices))

@router.callback_query(DeviceCountCB.filter())
async def change_device_count(query: CallbackQuery, callback_data: DeviceCountCB, state: FSMContext, settings: Settings):
    data = await state.get_data()
    if not data or 'tariff_slug' not in data:
        return await query.answer("Сессия истекла", show_alert=True)
        
    devices = data.get('devices', settings.default_devices)
    if callback_data.action == "inc":
        devices += 1
    elif callback_data.action == "dec" and devices > 2:
        devices -= 1
    else:
        return await query.answer()
        
    tariff = PREDEFINED_TARIFFS.get(data['tariff_slug'])
    base_price = get_price(tariff, devices, settings)
    promo_discount = data.get('promo_discount', 0)
    final_price = base_price * (100 - promo_discount) / 100.0
    
    await state.update_data(devices=devices, base_price=base_price, final_price=final_price)
    
    text = f"подтверждение\n\nтариф: {tariff['name']}\nустройств: {devices}\nсумма: {final_price:.2f} ₽"
    await query.message.edit_text(text, reply_markup=build_confirm_kb(devices))

@router.callback_query(F.data == "pay_promo")
async def ask_promo(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("введи промокод:")
    await state.set_state(PurchaseState.waiting_for_promo)

@router.message(PurchaseState.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext, promo_repo: PromoCodeRepository, settings: Settings):
    code = message.text.strip().lower()
    promo = await promo_repo.get_by_code(code)
    
    data = await state.get_data()
    tariff_slug = data.get('tariff_slug')
    
    def get_promo_fail_kb():
        builder = InlineKeyboardBuilder()
        builder.button(text="‹ назад", callback_data=TariffCB(slug=tariff_slug, action="buy").pack())
        return builder.as_markup()

    if not promo or not promo.is_active:
        return await message.answer("Промокод не найден или недействителен. Попробуй еще раз.", reply_markup=get_promo_fail_kb())
        
    if promo.expires_at and promo.expires_at < datetime.now():
        return await message.answer("Срок действия промокода истёк.", reply_markup=get_promo_fail_kb())
        
    if promo.max_uses > 0 and promo.uses_count >= promo.max_uses:
        return await message.answer("Лимит использований промокода исчерпан.", reply_markup=get_promo_fail_kb())
        
    tariff_slug = data['tariff_slug']
    devices = data.get('devices', settings.default_devices)
    tariff = PREDEFINED_TARIFFS[tariff_slug]
    base_price = data.get('base_price', get_price(tariff, devices, settings))
    
    final_price = base_price * (100 - promo.discount_percent) / 100.0
    await state.update_data(final_price=final_price, promo_id=promo.id, promo_discount=promo.discount_percent)
    
    text = f"промокод применен ({promo.discount_percent}%)\n\nтариф: {tariff['name']}\nустройств: {devices}\nновая сумма: {final_price:.2f} ₽"
    await message.answer(text, reply_markup=build_confirm_kb(devices))

@router.callback_query(F.data == "pay_confirm")
async def process_payment(
    query: CallbackQuery, 
    db_user: User,
    remnawave: RemnawaveClient,
    payment: PaymentProvider,
    order_repo: OrderRepository,
    sub_repo: SubscriptionRepository,
    promo_repo: PromoCodeRepository,
    state: FSMContext,
    settings: Settings
):
    data = await state.get_data()
    if not data or 'tariff_slug' not in data:
        return await query.answer("Сессия истекла", show_alert=True)
        
    tariff_slug = data['tariff_slug']
    final_price = data['final_price']
    promo_id = data['promo_id']
    devices = data.get('devices', settings.default_devices)
    tariff = PREDEFINED_TARIFFS.get(tariff_slug)
    
    # 1. Создаем заказ в БД
    order = await order_repo.add(Order(
        user_id=db_user.id,
        tariff_slug=tariff_slug,
        amount=final_price,
        promo_id=promo_id
    ))
    
    # 2. Вызов платежного провайдера (заглушка)
    pay_res = await payment.create_payment(final_price, f"Оплата тарифа {tariff_slug}", str(order.id), db_user.id)
    
    order.payment_id = pay_res.payment_id
    order.payment_status = pay_res.status.value
    await order_repo.update(order.id, payment_id=order.payment_id, payment_status=order.payment_status)
    
    if promo_id:
        promo = await promo_repo.get(promo_id)
        if promo:
            await promo_repo.update(promo.id, uses_count=promo.uses_count + 1)
    
    # 3. Создаем юзера в Remnawave (заглушка для теста)
    rw_username = f"sempre_tg{db_user.telegram_id}_{int(time.time())}"
    expire_date = datetime.now() + timedelta(days=tariff["days"])
    
    uuid_str = str(uuid.uuid4())
    sub_link = f"https://pan.project1000.ru/sub/{uuid_str}"
    
    uuid_str_2 = str(uuid.uuid4())
    sub_link_2 = f"https://pan.project1000.ru/sub/{uuid_str_2}"
    
    # 4. Запись подписки в БД
    sub = Subscription(
        user_id=db_user.id,
        tariff_slug=tariff_slug,
        remnawave_uuid=uuid_str,
        remnawave_username=rw_username,
        expires_at=expire_date,
        subscription_url=sub_link,
        subscription_url_2=sub_link_2,
        device_count=devices
    )
    sub = await sub_repo.add(sub)
    
    order.subscription_id = sub.id
    order.completed_at = datetime.now()
    await order_repo.update(order.id, subscription_id=sub.id, completed_at=order.completed_at)
    
    text = PURCHASE_SUCCESS.format(
        tariff=tariff["name"],
        expire_at=expire_date.strftime("%d.%m.%Y"),
        devices=devices
    )
    
    await query.message.edit_text(text)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="в главное меню", callback_data=MenuCB(action="back_to_main").pack())
    
    await query.message.answer(f"Ссылка 1:\n<code>{sub_link}</code>\n\nСсылка 2:\n<code>{sub_link_2}</code>", reply_markup=builder.as_markup())
    await state.clear()
