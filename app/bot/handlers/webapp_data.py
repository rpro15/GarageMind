# app/bot/handlers/webapp_data.py
from aiogram import Router, types
import json

router = Router()

@router.message(lambda msg: msg.web_app_data is not None)
async def handle_webapp_data(message: types.Message):
    data = message.web_app_data.data
    try:
        payload = json.loads(data)
        await message.answer(f"Спасибо! Ваш запрос: {payload.get('brand')} {payload.get('model')} получен.")
    except json.JSONDecodeError:
        await message.answer("Ошибка обработки данных.")