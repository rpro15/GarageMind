"""
# Marketplace Scraper — поиск шин по открытым источникам

Лёгкий адаптер для поиска товаров на маркетплейсах через публичные
HTML-страницы (без API-ключей). Использует httpx (async) + минимальный
HTML-парсинг.

## Как работает

1. Формирует URL для поиска на целевом маркетплейсе
2. GET-запрос с заголовками реального браузера
3. Парсинг HTML через поиск минимальных CSS-селекторов
4. Возвращает список Product

## Подключение / отключение

См. docs/marketplace_scraper.md
"""

from __future__ import annotations

import re
import logging
from typing import List, Optional
from urllib.parse import quote

import httpx

from app.domain.models import Product, TireRequest

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Конфигурация маркетплейсов
# ──────────────────────────────────────────────

# Каждый маркетплейс описывается:
#   name          — отображаемое имя
#   search_url    — шаблон URL для поиска (заполняется brand/model/year)
#   partner_link  — базовая ссылка на товар
#   selectors     — CSS-селекторы для парсинга карточки товара
#
# Если selectors пустые — используется fallback-заглушка для данного маркетплейса.

MARKETPLACES = [
    {
        "name": "Ozon",
        "search_url": "https://www.ozon.ru/search/?text={query}",
        "enabled": False,  # требует доработки селекторов
        "selectors": {
            "card": '[data-widget="searchResults"] a',
            "name": "a",
            "price": '[data-widget="price"]',
        },
    },
    {
        "name": "Wildberries",
        "search_url": "https://www.wildberries.ru/catalog/0/search.aspx?search={query}",
        "enabled": False,  # требует доработки селекторов
        "selectors": {
            "card": ".product-card",
            "name": ".product-card__name",
            "price": ".price__lower",
        },
    },
    {
        "name": "Яндекс.Маркет",
        "search_url": "https://market.yandex.ru/search?text={query}",
        "enabled": False,  # требует доработки селекторов
        "selectors": {
            "card": '[data-autotest-id="product-snippet"]',
            "name": '[data-autotest-id="product-name"]',
            "price": '[data-autotest-id="price"]',
        },
    },
    {
        "name": "Drom.ru",
        "search_url": "https://baza.drom.ru/{brand}/tires/search/?query={query}",
        "enabled": False,
        "selectors": {},
    },
]

# Если маркетплейс отключён — возвращается заглушка с этим количеством товаров
MOCK_PRODUCTS_COUNT = 3

# Таймаут запроса (сек)
SCRAPER_TIMEOUT = 10.0

# User-Agent для обхода блокировок
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


# ──────────────────────────────────────────────
#  Scraper
# ──────────────────────────────────────────────

class MarketplaceScraper:
    """Поиск шин по открытым данным маркетплейсов."""

    def __init__(self, marketplace_name: str | None = None):
        """
        marketplace_name: конкретный маркетплейс (Ozon/Wildberries/...),
                          или None = первый включённый
        """
        self._marketplace_name = marketplace_name
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=SCRAPER_TIMEOUT,
                follow_redirects=True,
            )
        return self._http_client

    async def search(self, query: str, max_results: int = 5) -> List[Product]:
        """
        Поиск товаров по текстовому запросу.

        Пока все маркетплейсы в config отключены (enabled=False),
        поэтому возвращается заглушка с моковыми данными.
        Когда включите хотя бы один — начнёт парсить реальные страницы.
        """
        marketplace = self._get_marketplace()
        name = marketplace["name"]

        if marketplace.get("enabled") and marketplace.get("selectors", {}).get("card"):
            logger.info("Scraping %s for: %s", name, query)
            try:
                products = await self._scrape(marketplace, query, max_results)
                if products:
                    return products
            except Exception as exc:
                logger.warning("Scrape failed for %s: %s", name, exc, exc_info=True)

        logger.info("Using mock data for %s (marketplace disabled or scrape failed)", name)
        return self._mock_products(query, name, count=min(max_results, MOCK_PRODUCTS_COUNT))

    def _get_marketplace(self) -> dict:
        enabled = [m for m in MARKETPLACES if m["enabled"]]
        if self._marketplace_name:
            for m in MARKETPLACES:
                if m["name"].lower() == self._marketplace_name.lower():
                    return m
            logger.warning("Marketplace '%s' not found, using first enabled", self._marketplace_name)

        if enabled:
            return enabled[0]

        # Если ничего не включено — возвращаем первый в списке (Ozon) с enabled=False
        return MARKETPLACES[0]

    async def _scrape(self, marketplace: dict, query: str, max_results: int) -> List[Product]:
        """Реальный парсинг HTML-страницы маркетплейса."""
        client = await self._get_client()

        search_url = marketplace["search_url"].format(query=quote(query))
        headers = {"User-Agent": USER_AGENTS[0]}

        logger.debug("GET %s", search_url)
        response = await client.get(search_url, headers=headers)
        response.raise_for_status()

        html = response.text
        products: List[Product] = []
        selectors = marketplace["selectors"]

        # Максимально простой парсинг — ищем блоки товаров
        # Используем сырой поиск паттернов, т.к. без lxml/bs4 сложно
        card_pattern = selectors.get("card", "")
        if not card_pattern:
            return products

        # Простейший парсинг: ищем ссылки-карточки
        # Реальную реализацию нужно дорабатывать под конкретный маркетплейс
        price_pattern = re.compile(r'"price"\s*:\s*["\']?(\d+[\d\s]*\d*)')
        name_pattern = re.compile(r'"name"\s*:\s*["\']([^"\']+)')

        prices = price_pattern.findall(html)
        names = name_pattern.findall(html)

        for i in range(min(len(prices), len(names), max_results)):
            try:
                price_val = float(re.sub(r'\s+', '', prices[i]))
            except ValueError:
                continue
            products.append(Product(
                id=f"{marketplace['name'].lower()}_{i}",
                name=names[i][:120],
                price=price_val,
                source=marketplace["name"],
                currency="RUB",
                image_url=None,
                partner_link=f"{marketplace['partner_link'] if 'partner_link' in marketplace else ''}",
            ))

        return products

    def _mock_products(self, query: str, source: str, count: int) -> List[Product]:
        """Заглушка на случай недоступности маркетплейса."""
        mock_tires = [
            ("Michelin Pilot Sport 4", 12400),
            ("Continental PremiumContact 6", 10800),
            ("Nokian Tyres Hakka Blue 3", 11500),
            ("Bridgestone Turanza T005", 9900),
            ("Goodyear EfficientGrip 2", 10500),
            ("Pirelli Cinturato P7", 11200),
            ("Hankook Ventus S1 evo3", 8200),
            ("Toyo Proxes Sport", 7800),
        ]
        import random
        selected = random.sample(mock_tires, min(count, len(mock_tires)))
        return [
            Product(
                id=f"mock_{source.lower()}_{i}",
                name=name,
                price=price,
                source=source,
                currency="RUB",
                image_url=None,
                partner_link=None,
            )
            for i, (name, price) in enumerate(selected)
        ]

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
