from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession

def create_engine(db_url: str) -> AsyncEngine:
    """Создает и возвращает асинхронный движок SQLAlchemy."""
    engine = create_async_engine(db_url, echo=False)
    return engine

def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Создает фабрику сессий."""
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
