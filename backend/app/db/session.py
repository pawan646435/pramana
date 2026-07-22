"""
Async SQLAlchemy engine + session factory.

Unlike app/db/cache.py's per-call Redis client, a module-level async
engine is the correct pattern here: SQLAlchemy's AsyncEngine manages its
own connection pool and is designed to be created once and shared, not
recreated per request. It doesn't bind to an event loop at construction
time the way the Redis client did.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
