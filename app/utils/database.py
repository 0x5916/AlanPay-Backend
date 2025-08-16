from typing import Annotated, AsyncGenerator, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

from app.utils.config import settings
from app.utils.logging_config import logger


engine: AsyncEngine = create_async_engine(
    url=settings.asyncpg_url.unicode_string(), echo=True, future=True
).execution_options(is_async=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    future=True
)

async def create_db_and_tables() -> None:
    logger.info("Creating database")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    return

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


AsyncSessionDep: TypeAlias = Annotated[AsyncSession, Depends(get_session)]
