from __future__ import annotations

"""Main conversation handlers: /start → car setup → results."""

import os
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.handlers import api_client
from bot.handlers.keyboards import (
    category_kb,
    results_kb,
    season_kb,
    style_kb,
)
from bot.handlers.states import CarSetup

MINIAPP_URL = os.getenv("MINIAPP_URL", "")  # Telegram Mini App URL

router = Router()


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    text = (
        "👋 Привет! Я <b>GarageMind</b> — ваш AI-помощник по подбору шин и дисков.\n\n"
        "Не читай форумы — просто спроси!\n\n"
        "Введите марку вашего автомобиля (например: <b>Toyota</b>):"
    )

    # Show Mini App button if URL is configured
    if MINIAPP_URL:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="🚗 Открыть подборщик",
                    web_app={"url": MINIAPP_URL},
                )
            ]]
        )
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML")

    await state.set_state(CarSetup.waiting_make)


# ------------------------------------------------------------------
# Car make
# ------------------------------------------------------------------

@router.message(CarSetup.waiting_make)
async def handle_make(message: Message, state: FSMContext) -> None:
    make = (message.text or "").strip()
    if not make:
        await message.answer("Пожалуйста, введите марку автомобиля.")
        return

    try:
        models = api_client.fetch_models(make)
    except Exception:
        models = []

    await state.update_data(car_make=make)

    if models:
        # Build a quick-reply-style inline keyboard with known models
        builder = InlineKeyboardBuilder()
        for m in models[:8]:
            builder.button(text=m, callback_data=f"model:{m}")
        builder.adjust(2)
        await message.answer(
            f"Выберите модель <b>{make}</b> или введите вручную:",
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
        )
    else:
        await message.answer(
            f"Введите модель <b>{make}</b>:",
            parse_mode="HTML",
        )

    await state.set_state(CarSetup.waiting_model)


# ------------------------------------------------------------------
# Car model — via callback or free text
# ------------------------------------------------------------------

@router.callback_query(CarSetup.waiting_model, F.data.startswith("model:"))
async def handle_model_callback(callback: CallbackQuery, state: FSMContext) -> None:
    model = callback.data.split(":", 1)[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    await _ask_year(callback.message, state, model)


@router.message(CarSetup.waiting_model)
async def handle_model_text(message: Message, state: FSMContext) -> None:
    model = (message.text or "").strip()
    if not model:
        await message.answer("Пожалуйста, введите модель автомобиля.")
        return
    await _ask_year(message, state, model)


async def _ask_year(message: Message, state: FSMContext, model: str) -> None:
    await state.update_data(car_model=model)
    await message.answer("Введите год выпуска (например: <b>2021</b>):", parse_mode="HTML")
    await state.set_state(CarSetup.waiting_year)


# ------------------------------------------------------------------
# Year
# ------------------------------------------------------------------

@router.message(CarSetup.waiting_year)
async def handle_year(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        year = int(text)
        if not (1900 <= year <= 2027):
            raise ValueError
    except ValueError:
        await message.answer("Введите корректный год (например: 2020).")
        return

    await state.update_data(car_year=year)
    await message.answer("Что подбираем?", reply_markup=category_kb())
    await state.set_state(CarSetup.waiting_category)


# ------------------------------------------------------------------
# Category
# ------------------------------------------------------------------

@router.callback_query(CarSetup.waiting_category, F.data.startswith("cat:"))
async def handle_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Выберите сезон:", reply_markup=season_kb())
    await state.set_state(CarSetup.waiting_season)


# ------------------------------------------------------------------
# Season
# ------------------------------------------------------------------

@router.callback_query(CarSetup.waiting_season, F.data.startswith("season:"))
async def handle_season(callback: CallbackQuery, state: FSMContext) -> None:
    season = callback.data.split(":", 1)[1]
    await state.update_data(season=season)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Стиль вождения:", reply_markup=style_kb())
    await state.set_state(CarSetup.waiting_style)


# ------------------------------------------------------------------
# Driving style
# ------------------------------------------------------------------

@router.callback_query(CarSetup.waiting_style, F.data.startswith("style:"))
async def handle_style(callback: CallbackQuery, state: FSMContext) -> None:
    style = callback.data.split(":", 1)[1]
    await state.update_data(driving_style=style)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Введите ваш бюджет в рублях (например: <b>30000</b>):", parse_mode="HTML"
    )
    await state.set_state(CarSetup.waiting_budget)


# ------------------------------------------------------------------
# Budget → fetch & display results
# ------------------------------------------------------------------

@router.message(CarSetup.waiting_budget)
async def handle_budget(message: Message, state: FSMContext) -> None:
    text = (message.text or "").replace(" ", "").strip()
    try:
        budget = int(text)
        if budget <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите бюджет числом (например: 30000).")
        return

    await state.update_data(budget_rub=budget)
    data = await state.get_data()
    await state.clear()

    await message.answer("⏳ Подбираю варианты...")

    try:
        result = api_client.fetch_recommendations(
            car_make=data["car_make"],
            car_model=data["car_model"],
            car_year=data["car_year"],
            category=data["category"],
            season=data["season"],
            driving_style=data["driving_style"],
            budget_rub=data["budget_rub"],
        )
    except Exception as exc:
        await message.answer(f"❌ Ошибка при подборе: {exc}\n\nПопробуйте /start снова.")
        return

    recommendations = result.get("recommendations", [])
    if not recommendations:
        await message.answer(
            "😔 По вашим параметрам ничего не нашлось.\n"
            "Попробуйте увеличить бюджет или изменить критерии. /start"
        )
        return

    _CATEGORY_RU = {"tires": "Шины", "wheels": "Диски"}
    _SEASON_RU = {"winter": "зима", "summer": "лето", "all_season": "всесезон"}
    _STYLE_RU = {"comfort": "комфорт", "sport": "спорт", "offroad": "бездорожье"}

    header = (
        f"🚗 <b>{data['car_make']} {data['car_model']} {data['car_year']}</b>\n"
        f"📦 {_CATEGORY_RU.get(data['category'], data['category'])} · "
        f"{_SEASON_RU.get(data['season'], data['season'])} · "
        f"{_STYLE_RU.get(data['driving_style'], data['driving_style'])}\n"
        f"💳 Бюджет: до {budget:,} ₽\n\n"
        f"<b>Лучшие варианты:</b>"
    )

    lines = []
    for rec in recommendations:
        partner_badge = "⭐" if rec.get("is_partner") else ""
        lines.append(
            f"{rec['rank']}. {partner_badge}<b>{rec['product_name']}</b>\n"
            f"   💰 {rec['price_rub']:,} ₽ · {rec['marketplace'].upper()}"
        )

    body = "\n\n".join(lines)
    await message.answer(
        f"{header}\n\n{body}",
        parse_mode="HTML",
        reply_markup=results_kb(recommendations),
    )
