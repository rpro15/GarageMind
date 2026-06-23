# app/bot/handlers/start.py
from aiogram import Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from app.config.settings import settings

router = Router()

@router.message(lambda msg: msg.text == "/start")
async def start_command(message: types.Message):
    webapp_url = settings.MINIAPP_URL
    web_app_button = KeyboardButton(
        text="🔧 Подобрать шины",
        web_app=WebAppInfo(url=webapp_url)
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[web_app_button]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(
        "👋 Привет! Я <b>GarageMind</b> – твой персональный помощник по подбору автозапчастей.\n\n"
        "Сейчас я помогу подобрать шины для твоего авто. Нажми кнопку ниже, чтобы открыть <b>Mini App</b>.",
        reply_markup=keyboard
    )

@router.message(lambda msg: msg.text == "/help")
async def help_command(message: types.Message):
    await message.answer(
        "Я помогаю подбирать автозапчасти.\n"
        "Просто открой Mini App, выбери свой автомобиль, и я покажу рекомендации."
    )