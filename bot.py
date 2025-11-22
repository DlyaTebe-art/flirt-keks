import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db
from handlers.create_ad import create_ad_router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def main():
    # ініціалізація БД
    await init_db()

    # створення бота з новим підходом
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher(storage=MemoryStorage())

    # реєструємо роутер
    dp.include_router(create_ad_router)

    print("Бот запущено...")

    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
