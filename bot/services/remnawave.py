from typing import Optional
from datetime import datetime
import aiohttp
import logging

logger = logging.getLogger(__name__)

class RemnawaveClient:
    """Async HTTP client для взаимодействия с Remnawave Panel API."""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Remnawave API error: {method} {url} - {e}")
            raise

    async def create_user(
        self,
        username: str,
        traffic_limit_bytes: int = 0,
        expire_at: Optional[datetime] = None,
        telegram_id: Optional[int] = None,
    ) -> dict:
        """POST /api/users — создать пользователя в панели."""
        data = {
            "username": username,
            "data_limit": traffic_limit_bytes,
        }
        if expire_at:
            data["expire_at"] = int(expire_at.timestamp())
        if telegram_id:
            data["note"] = f"tg_{telegram_id}"
            
        return await self._request("POST", "/api/users", json=data)

    async def get_user(self, uuid: str) -> dict:
        """GET /api/users/{uuid} — получить информацию о пользователе."""
        return await self._request("GET", f"/api/users/{uuid}")

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """GET /api/users/by-username/{username}"""
        try:
            return await self._request("GET", f"/api/users/by-username/{username}")
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return None
            raise

    async def update_user(self, uuid: str, **kwargs) -> dict:
        """PUT /api/users/{uuid} — обновить параметры пользователя."""
        return await self._request("PUT", f"/api/users/{uuid}", json=kwargs)

    async def delete_user(self, uuid: str) -> bool:
        """DELETE /api/users/{uuid} — удалить пользователя."""
        await self._request("DELETE", f"/api/users/{uuid}")
        return True

    async def disable_user(self, uuid: str) -> dict:
        """POST /api/users/{uuid}/disable"""
        return await self._request("POST", f"/api/users/{uuid}/disable")

    async def enable_user(self, uuid: str) -> dict:
        """POST /api/users/{uuid}/enable"""
        return await self._request("POST", f"/api/users/{uuid}/enable")

    async def get_user_usage(self, uuid: str) -> dict:
        """Получить статистику использования трафика."""
        # У remnawave статистика возвращается в GET /api/users/{uuid}
        # Но если есть отдельный эндпоинт, используем его. 
        # Предполагаем GET /api/users/{uuid}/usage или берем из get_user
        user = await self.get_user(uuid)
        return {
            "used_bytes": user.get("used_traffic", 0),
            "limit_bytes": user.get("data_limit", 0)
        }

    async def revoke_user_subscription(self, uuid: str) -> dict:
        """POST /api/users/{uuid}/revoke-subscription — пересоздать ключ."""
        return await self._request("POST", f"/api/users/{uuid}/revoke-subscription")

    async def get_all_users(self) -> list[dict]:
        """GET /api/users — список всех пользователей."""
        return await self._request("GET", "/api/users")

    async def get_subscription_link(self, short_uuid: str) -> str:
        """Сформировать subscription URL для пользователя."""
        # В Remnawave это обычно /{short_uuid} или /sub/{short_uuid}
        return f"{self.base_url}/sub/{short_uuid}"

    async def get_system_stats(self) -> dict:
        """GET /api/system — общая статистика системы."""
        return await self._request("GET", "/api/system")

    async def get_inbounds(self) -> list[dict]:
        """GET /api/inbounds — список доступных inbound-ов."""
        return await self._request("GET", "/api/inbounds")
