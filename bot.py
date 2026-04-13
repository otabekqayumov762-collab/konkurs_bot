import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user

async def main():
    logging.basicConfig(level=logging.INFO)
    
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is not set in environment or .env file.")
        return

    # Initialize Bot and Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Include routers from handlers
    dp.include_router(user.router)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        pass
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
