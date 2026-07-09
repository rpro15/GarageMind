"""Сервис сравнения шин.

Позволяет пользователю выбрать 2–3 товара и получить таблицу сравнения
(цена, характеристики, износостойкость, шумность, сцепление).
"""
from __future__ import annotations

import logging
from typing import List
from dataclasses import dataclass, field

from app.domain.models import Product
from app.ports.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class ComparisonItem:
    """Одна строка в таблице сравнения."""
    name: str
    price: str
    rating: str
    pros: str
    cons: str
    best_for: str


@dataclass
class ComparisonResult:
    """Результат сравнения шин."""
    products: List[ComparisonItem]
    summary: str  # краткий вывод от AI
    raw_advice: str  # полный ответ AI


class ProductComparisonService:
    """
    Сравнение 2–3 товаров между собой.

    Использует DeepSeek для генерации таблицы сравнения
    и краткого вывода "что лучше для чего".
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def compare(self, products: List[Product]) -> ComparisonResult:
        """
        Сравнить выбранные товары.

        Args:
            products: список товаров (2–3 шт.)

        Returns:
            ComparisonResult с таблицей и выводом
        """
        if len(products) < 2:
            raise ValueError("Нужно минимум 2 товара для сравнения")
        if len(products) > 4:
            raise ValueError("Максимум 4 товара для сравнения")

        prompt = self._build_comparison_prompt(products)
        system_prompt = self._system_prompt()

        # Получаем ответ от DeepSeek
        advice = await self.llm.generate_text(prompt, system_prompt=system_prompt)

        # Парсим результат
        items = []
        for p in products:
            items.append(ComparisonItem(
                name=p.name,
                price=f"{p.price:,.0f} {p.currency}",
                rating=f"{p.rating}/5" if p.rating else "нет данных",
                pros="",
                cons="",
                best_for="",
            ))

        # Извлекаем краткий вывод
        summary = self._extract_summary(advice)

        return ComparisonResult(
            products=items,
            summary=summary,
            raw_advice=advice,
        )

    def _system_prompt(self) -> str:
        return (
            "Ты — эксперт по автомобильным шинам. "
            "Твоя задача — сравнить несколько моделей шин и помочь пользователю выбрать лучшую. "
            "Отвечай структурированно: таблица сравнения, затем краткий вывод."
        )

    def _build_comparison_prompt(self, products: List[Product]) -> str:
        """Сформировать промпт для сравнения."""
        parts = ["Сравни следующие шины между собой:\n"]

        for i, p in enumerate(products, 1):
            parts.append(
                f"{i}. {p.name}"
                f"{' (⭐ ' + str(p.rating) + '/5)' if p.rating else ''}"
                f" — {p.price:,.0f} {p.currency}"
                f" от {p.source or 'неизвестного продавца'}"
            )

        parts.append("""
Сделай таблицу сравнения по критериям:
- Цена
- Износостойкость
- Шумность
- Сцепление на мокрой дороге
- Сцепление на сухой дороге
- Для какого стиля вождения подходит (спорт/комфорт/эконом)
- Для какого сезона

После таблицы напиши краткий вывод:
- Какие шины лучше для города
- Какие для трассы
- Какие для спортивной езды
- Что лучше по цене/качеству

Ответ оформи красиво, используй эмодзи.""")
        return "\n".join(parts)

    @staticmethod
    def _extract_summary(advice: str) -> str:
        """Извлечь краткий вывод из ответа AI."""
        # Ищем раздел "вывод" или "итог"
        import re
        patterns = [
            r"(?:вывод|итог|резюме)[:\s]*([^\n]*(?:\n(?!Таблица|##)[^\n]*)*)",
            r"(?:рекомендую|лучше всего|советую)[:\s]*([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, advice, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:300]
        # Если не нашли — возвращаем последние 300 символов
        return advice[-300:].strip() if len(advice) > 300 else advice
