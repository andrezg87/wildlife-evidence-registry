import asyncpg

from app.config import settings

pool: asyncpg.Pool | None = None


async def connect_to_database() -> None:
    global pool
    pool = await asyncpg.create_pool(dsn=settings.database_url)


async def disconnect_from_database() -> None:
    if pool is not None:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool
