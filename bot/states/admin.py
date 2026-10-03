from aiogram.fsm.state import State, StatesGroup

class AdminPromoState(StatesGroup):
    waiting_for_code = State()
    waiting_for_discount = State()
    waiting_for_max_uses = State()
    waiting_for_days_valid = State()

class AdminTicketState(StatesGroup):
    waiting_for_reply = State()
