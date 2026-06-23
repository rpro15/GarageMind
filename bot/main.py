from __future__ import annotations

"""GarageMind Telegram bot entry point.

Run:
    python -m bot.main

Environment variables:
    BOT_TOKEN         — required, Telegram Bot token from @BotFather
    API_BASE_URL      — URL of the Flask API service (default: http://api:8000)
    MINIAPP_URL       — Telegram Mini App HTTPS URL (optional)
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.conversation import router


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


async def main() -> None:
    configure_logging()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required.")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logging.info("Starting GarageMind bot…")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
