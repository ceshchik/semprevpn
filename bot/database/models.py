from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class GlobalSettings(Base):
    __tablename__ = "global_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    allow_refunds: Mapped[bool] = mapped_column(default=False)

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]]
    first_name: Mapped[Optional[str]]
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    referral_code: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    referred_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tariff_slug: Mapped[str]
    remnawave_uuid: Mapped[str] = mapped_column(unique=True)
    remnawave_username: Mapped[str]
    subscription_url: Mapped[Optional[str]]
    subscription_url_2: Mapped[Optional[str]] = mapped_column(nullable=True)
    device_count: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(default="active")  # active, expired, disabled
    started_at: Mapped[datetime] = mapped_column(default=func.now())
    expires_at: Mapped[datetime]
    
    user: Mapped["User"] = relationship(back_populates="subscriptions")


class PromoCode(Base):
    __tablename__ = "promo_codes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(unique=True, index=True)
    discount_percent: Mapped[int]  # Скидка в процентах (0-100)
    max_uses: Mapped[int]  # Максимальное количество использований (0 - без ограничений)
    uses_count: Mapped[int] = mapped_column(default=0)  # Сколько раз уже использован
    expires_at: Mapped[Optional[datetime]]  # До какого времени действует
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subscription_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)
    promo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("promo_codes.id"), nullable=True)
    tariff_slug: Mapped[str]
    amount: Mapped[float]
    currency: Mapped[str] = mapped_column(default="RUB")
    payment_id: Mapped[Optional[str]]
    payment_status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    completed_at: Mapped[Optional[datetime]]


class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str]
    status: Mapped[str] = mapped_column(default="open")  # open, in_progress, closed
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    closed_at: Mapped[Optional[datetime]]
    
    user: Mapped["User"] = relationship()
    messages: Mapped[list["TicketMessage"]] = relationship(back_populates="ticket")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    sender_type: Mapped[str]  # "user" или "admin"
    sender_id: Mapped[int]  # telegram_id
    text: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    ticket: Mapped["Ticket"] = relationship(back_populates="messages")
