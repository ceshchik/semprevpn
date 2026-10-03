from bot.database.repositories.base import BaseRepository
from bot.database.models import Order

class OrderRepository(BaseRepository[Order]):
    def __init__(self, session):
        super().__init__(session, Order)
