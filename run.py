import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from app.database.models import async_main

from app.handlers import router as handlers
from app.static import router as static

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()



async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await async_main()
    dp.include_routers(
        handlers,
        static
        )
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')