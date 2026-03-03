import asyncpg
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
 'postgresql://neondb_owner:npg_Ptk3gGhlCpB7@ep-fragrant-salad-adpreuqa-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
)

_pool: asyncpg.Pool = None


async def create_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    return _pool