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

# connect_args here work around two Neon-specific quirks on the pooled
# ("-pooler") endpoint:
#
# - statement_cache_size=0: asyncpg caches prepared statements per
#   physical connection by default. Neon's pooler runs PgBouncer in
#   transaction-pooling mode, which can hand a client a different
#   physical connection between statements - so a statement prepared on
#   one connection can be replayed against another that never prepared
#   it, surfacing as "prepared statement ... does not exist" under real
#   traffic. This is a documented asyncpg/PgBouncer interaction, not
#   specific to this app. Disabling asyncpg's statement cache avoids it.
# - ssl="require": Neon's connection strings normally carry
#   ?sslmode=require as a libpq/psycopg2-style URL query param, which
#   asyncpg does not parse the same way - passed as a URL param it's
#   silently ignored rather than erroring, so SSL must be requested
#   explicitly via a connect() argument instead.
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"ssl": "require", "statement_cache_size": 0},
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
