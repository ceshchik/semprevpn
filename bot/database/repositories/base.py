from typing import Generic, TypeVar, Type, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from bot.database.models import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model_class: Type[ModelType]):
        self.session = session
        self.model_class = model_class

    async def get(self, id: int) -> Optional[ModelType]:
        result = await self.session.execute(select(self.model_class).where(self.model_class.id == id))
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[ModelType]:
        result = await self.session.execute(select(self.model_class))
        return result.scalars().all()

    async def add(self, model: ModelType) -> ModelType:
        self.session.add(model)
        await self.session.flush()
        return model

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        stmt = update(self.model_class).where(self.model_class.id == id).values(**kwargs).returning(self.model_class)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        stmt = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
