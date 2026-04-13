import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user
from utils.database import init_db

async def main():
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is not set in environment or .env file.")
        return

    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user.router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        pass
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
