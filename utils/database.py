import asyncpg
from config import DATABASE_URL

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                payment_intent TEXT,
                receipt_sent BOOLEAN DEFAULT FALSE,
                registered_at TIMESTAMP DEFAULT NOW()
            )
        """)

async def save_registration(user_id: int, username: str, full_name: str,
                             phone: str, payment_intent: str, receipt_sent: bool = False):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO registrations (user_id, username, full_name, phone, payment_intent, receipt_sent)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, username, full_name, phone, payment_intent, receipt_sent)

async def get_all_registrations():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT id, user_id, username, full_name, phone, payment_intent, receipt_sent, registered_at
            FROM registrations ORDER BY registered_at DESC
        """)

async def get_all_user_ids():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT DISTINCT user_id FROM registrations")
        return [r["user_id"] for r in rows]
