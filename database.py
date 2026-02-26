import aiosqlite
from config import DATABASE_URL

async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                referrer_id INTEGER,
                points INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT NOT NULL,
                channel_link TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contest_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_active INTEGER DEFAULT 0
            )
        """)
        # Default contest settings
        await db.execute("INSERT OR IGNORE INTO contest_settings (id, is_active) VALUES (1, 0)")
        await db.commit()

# ========== USER FUNCTIONS ==========

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def create_user(telegram_id: int, username: str, full_name: str, referrer_id: int = None):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, full_name, referrer_id) VALUES (?, ?, ?, ?)",
            (telegram_id, username, full_name, referrer_id)
        )
        await db.commit()

async def add_points(telegram_id: int, points: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE users SET points = points + ? WHERE telegram_id = ?", (points, telegram_id))
        await db.commit()

async def set_points(telegram_id: int, points: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE users SET points = ? WHERE telegram_id = ?", (points, telegram_id))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY points DESC") as cursor:
            return await cursor.fetchall()

async def get_user_referrals(telegram_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE referrer_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchall()

async def get_top_users(limit: int = 10):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY points DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

async def reset_all_data():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        await db.commit()

# ========== CHANNEL FUNCTIONS ==========

async def get_channels():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels") as cursor:
            return await cursor.fetchall()

async def add_channel(channel_id: str, channel_name: str, channel_link: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "INSERT OR IGNORE INTO channels (channel_id, channel_name, channel_link) VALUES (?, ?, ?)",
            (channel_id, channel_name, channel_link)
        )
        await db.commit()

async def remove_channel(channel_id: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        await db.commit()

# ========== CONTEST FUNCTIONS ==========

async def get_contest_status():
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("SELECT is_active FROM contest_settings WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def set_contest_status(is_active: bool):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE contest_settings SET is_active = ? WHERE id = 1", (int(is_active),))
        await db.commit()
