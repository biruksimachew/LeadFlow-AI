import asyncpg

from app.config import settings


async def create_database_pool() -> asyncpg.Pool:
    """
    Create a PostgreSQL connection pool.

    LeadFlow uses Supabase PostgreSQL as its operational
    and audit database.
    """
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        command_timeout=10,
    )


async def database_is_alive(pool: asyncpg.Pool) -> bool:
    async with pool.acquire() as connection:
        result = await connection.fetchval("select 1;")

    return result == 1