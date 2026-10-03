from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    bot_token: str
    admin_ids: list[int]  # Список telegram_id администраторов
    
    # Remnawave
    remnawave_url: str       # Например: https://panel.example.com
    remnawave_api_token: str
    
    # Payment
    payment_provider: str = "stub"  # "stub" | "yookassa" | "cryptobot"
    
    # Devices
    default_devices: int = 2
    extra_device_price: int = 40
    
    # Database
    database_url: str = "sqlite+aiosqlite:///data/sempre.db"
    
    # Bot settings
    support_chat_id: Optional[int] = None  # Группа для пересылки тикетов (опционально)
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
