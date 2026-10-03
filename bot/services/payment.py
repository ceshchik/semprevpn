from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@dataclass
class PaymentResult:
    payment_id: str
    status: PaymentStatus
    amount: float
    currency: str = "RUB"
    payment_url: Optional[str] = None
    metadata: Optional[dict] = None

class PaymentProvider(ABC):
    """Абстрактный провайдер оплаты."""
    
    @abstractmethod
    async def create_payment(
        self,
        amount: float,
        description: str,
        order_id: str,
        user_id: int,
    ) -> PaymentResult:
        """Создать платёж."""
        pass
    
    @abstractmethod
    async def check_payment(self, payment_id: str) -> PaymentResult:
        """Проверить статус платежа."""
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str) -> PaymentResult:
        """Вернуть платёж."""
        pass


class StubPaymentProvider(PaymentProvider):
    """
    Заглушка для тестирования.
    Автоматически подтверждает все платежи.
    """
    
    async def create_payment(self, amount, description, order_id, user_id):
        return PaymentResult(
            payment_id=f"stub_{order_id}",
            status=PaymentStatus.COMPLETED,
            amount=amount,
        )
    
    async def check_payment(self, payment_id):
        return PaymentResult(
            payment_id=payment_id,
            status=PaymentStatus.COMPLETED,
            amount=0,
        )
    
    async def refund_payment(self, payment_id):
        return PaymentResult(
            payment_id=payment_id,
            status=PaymentStatus.REFUNDED,
            amount=0,
        )
