from webapp.api_server import start_api
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db, get_deadline, get_contest_status, set_contest_status, get_top_users, get_all_users, clear_deadline
from handlers import user, admin

logging.basicConfig(level=logging.INFO)


async def deadline_checker(bot: Bot):
    """Har 60 sekundda deadline ni tekshiradi"""
    while True:
        try:
            is_active = await get_contest_status()
            if is_active:
                deadline_str = await get_deadline()
                if deadline_str:
                    deadline = datetime.fromisoformat(deadline_str)
                    now = datetime.now()
                    if now >= deadline:
                        # Konkursni avtomatik yakunlash
                        await set_contest_status(False)
                        await clear_deadline()

                        # G'oliblarni aniqlash va e'lon qilish
                        top_users = await get_top_users(3)
                        medals = ["🥇", "🥈", "🥉"]
                        lines = ["⏰ <b>KONKURS MUDDATI TUGADI!</b>\n\n🏆 <b>G'OLIBLAR:</b>\n"]
                        for i, u in enumerate(top_users):
                            name = u["full_name"] or u["username"] or "Nomsiz"
                            lines.append(f"{medals[i]} {i+1}-o'rin: <b>{name}</b> — {u['points']} ball")

                        announcement = "\n".join(lines)
                        all_users = await get_all_users()
                        for user_row in all_users:
                            try:
                                await bot.send_message(user_row["telegram_id"], announcement, parse_mode="HTML")
                            except Exception:
                                pass

                        logging.info("Konkurs avtomatik yakunlandi!")
        except Exception as e:
            logging.error(f"Deadline checker xato: {e}")

        await asyncio.sleep(60)


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(admin.router)
    dp.include_router(user.router)
    await start_api(None)

    # Deadline checker ni parallel ishlatish
    asyncio.create_task(deadline_checker(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
