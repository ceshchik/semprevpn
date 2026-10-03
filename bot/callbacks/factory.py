from aiogram.filters.callback_data import CallbackData

class MenuCB(CallbackData, prefix="menu"):
    action: str  # "tariffs", "subscriptions", "support", "profile"

class TariffCB(CallbackData, prefix="tariff"):
    slug: str  # "lite", "base", "comfort"
    action: str = "view"  # "view", "buy"

class SubscriptionCB(CallbackData, prefix="sub"):
    id: int
    action: str  # "details", "renew", "key", "instructions"

class TicketCB(CallbackData, prefix="ticket"):
    id: int
    action: str  # "view", "reply", "close"

class AdminCB(CallbackData, prefix="admin"):
    action: str  # "stats", "tickets", "broadcast", "user_lookup"

class PaymentCB(CallbackData, prefix="pay"):
    order_id: int
    action: str  # "confirm", "cancel"

class DeviceCountCB(CallbackData, prefix="dev"):
    action: str  # "inc", "dec"
