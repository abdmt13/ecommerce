from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class Database:
    def __init__(self, *, database_url: str) -> None:
        if not database_url.startswith(("postgresql+asyncpg://", "mysql+asyncmy://")):
            raise ValueError("DATABASE_URL debe usar postgresql+asyncpg:// o mysql+asyncmy://")
        self.engine = create_async_engine(database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        await self.engine.dispose()
