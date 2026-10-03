from aiogram.fsm.state import State, StatesGroup

class PurchaseState(StatesGroup):
    confirm_tariff = State()
    waiting_for_promo = State()
    waiting_for_payment = State()
