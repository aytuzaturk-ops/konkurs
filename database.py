import asyncpg
from config import DATABASE_URL

# Connection pool
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return pool

async def init_db():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                referrer_id BIGINT,
                points INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Channels table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT NOT NULL,
                channel_link TEXT NOT NULL
            )
        """)
        
        # Contest settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS contest_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_active INTEGER DEFAULT 0,
                deadline TEXT DEFAULT NULL
            )
        """)
        
        # Insert default contest settings
        await conn.execute("""
            INSERT INTO contest_settings (id, is_active, deadline) 
            VALUES (1, 0, NULL) 
            ON CONFLICT (id) DO NOTHING
        """)

async def get_user(telegram_id: int):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        return dict(row) if row else None

async def create_user(telegram_id: int, username: str, full_name: str, referrer_id: int = None):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (telegram_id, username, full_name, referrer_id) 
               VALUES ($1, $2, $3, $4) ON CONFLICT (telegram_id) DO NOTHING""",
            telegram_id, username, full_name, referrer_id
        )

async def add_points(telegram_id: int, points: int):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = points + $1 WHERE telegram_id = $2", points, telegram_id)

async def set_points(telegram_id: int, points: int):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = $1 WHERE telegram_id = $2", points, telegram_id)

async def get_all_users():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY points DESC")
        return [dict(row) for row in rows]

async def get_user_referrals(telegram_id: int):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users WHERE referrer_id = $1", telegram_id)
        return [dict(row) for row in rows]

async def get_top_users(limit: int = 100):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY points DESC LIMIT $1", limit)
        return [dict(row) for row in rows]

async def reset_all_data():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE")

async def get_today_users_count():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM users WHERE DATE(joined_at) = CURRENT_DATE"
        )
        return row[0] if row else 0

async def get_total_referrals_count():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM users WHERE referrer_id IS NOT NULL"
        )
        return row[0] if row else 0

async def get_top_referrers(limit: int = 5):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.telegram_id, u.full_name, u.username, u.points,
                   COUNT(r.id) as ref_count
            FROM users u
            LEFT JOIN users r ON r.referrer_id = u.telegram_id
            GROUP BY u.telegram_id, u.full_name, u.username, u.points
            ORDER BY ref_count DESC
            LIMIT $1
        """, limit)
        return [dict(row) for row in rows]

async def get_channels():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM channels")
        return [dict(row) for row in rows]

async def add_channel(channel_id: str, channel_name: str, channel_link: str):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO channels (channel_id, channel_name, channel_link) 
               VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO NOTHING""",
            channel_id, channel_name, channel_link
        )

async def remove_channel(channel_id: str):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("DELETE FROM channels WHERE channel_id = $1", channel_id)

async def get_contest_status():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT is_active FROM contest_settings WHERE id = 1")
        return bool(row[0]) if row else False

async def set_contest_status(is_active: bool):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("UPDATE contest_settings SET is_active = $1 WHERE id = 1", int(is_active))

async def get_deadline():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT deadline FROM contest_settings WHERE id = 1")
        return row[0] if row else None

async def set_deadline(deadline: str):
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("UPDATE contest_settings SET deadline = $1 WHERE id = 1", deadline)

async def clear_deadline():
    conn_pool = await get_pool()
    async with conn_pool.acquire() as conn:
        await conn.execute("UPDATE contest_settings SET deadline = NULL WHERE id = 1")
