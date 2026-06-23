# app/bot/dispatcher.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config.settings import settings
from app.bot.handlers import start, webapp_data
import logging

logger = logging.getLogger(__name__)

async def start_bot():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.include_router(start.router)
    dp.include_router(webapp_data.router)
    
    logger.info("Bot started polling...")
    await dp.start_polling(bot)