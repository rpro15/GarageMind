from __future__ import annotations

"""Keyboards used across bot handlers."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def category_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Шины", callback_data="cat:tires")
    builder.button(text="💿 Диски", callback_data="cat:wheels")
    builder.adjust(2)
    return builder.as_markup()


def season_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❄️ Зима", callback_data="season:winter")
    builder.button(text="☀️ Лето", callback_data="season:summer")
    builder.button(text="🌤 Всесезон", callback_data="season:all_season")
    builder.adjust(2)
    return builder.as_markup()


def style_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="😌 Комфорт", callback_data="style:comfort")
    builder.button(text="🏎 Спорт", callback_data="style:sport")
    builder.button(text="🚙 Бездорожье", callback_data="style:offroad")
    builder.adjust(2)
    return builder.as_markup()


def results_kb(recommendations: list[dict]) -> InlineKeyboardMarkup:
    """Inline keyboard with one 'Buy' button per recommendation."""
    builder = InlineKeyboardBuilder()
    for rec in recommendations:
        label = f"💰 {rec['product_name'][:30]} — {rec['price_rub']:,} ₽"
        builder.button(text=label, url=rec["affiliate_url"])
    builder.adjust(1)
    return builder.as_markup()
