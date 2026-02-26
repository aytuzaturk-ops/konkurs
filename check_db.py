import asyncio
import aiosqlite

async def test():
    async with aiosqlite.connect('contest.db') as db:
        async with db.execute("SELECT * FROM channels") as cursor:
            rows = await cursor.fetchall()
            print("KANALLAR:", rows)
        async with db.execute("SELECT * FROM contest_settings") as cursor:
            print("KONKURS:", await cursor.fetchone())

asyncio.run(test())