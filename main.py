import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_BOT_TOKEN
from handlers.user import router
from utils.memory import init_db, close_db

logging.basicConfig(level=logging.INFO)


async def main():
    # aiogram>=3.7 removed parse_mode from Bot initializer
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=None),
    )

    # Persistent memory (Postgres)
    await init_db()

    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())